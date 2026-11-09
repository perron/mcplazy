"""Lazy MCP gateway: a few catalog tools instead of every backend schema."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

__version__ = "0.1.0"

PROTOCOL_VERSION = "2024-11-05"


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, (len(text.encode("utf-8")) + 3) // 4)


def load_catalog(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "tools" in data:
        tools = data["tools"]
    elif isinstance(data, list):
        tools = data
    else:
        raise ValueError("catalog must be a tool array or an object with a tools array")
    cleaned = []
    for tool in tools:
        name = tool.get("name")
        if not name:
            raise ValueError("every catalog tool needs a name")
        cleaned.append({
            "name": name,
            "description": tool.get("description") or "",
            "inputSchema": tool.get("inputSchema") or tool.get("input_schema") or {"type": "object"},
            "result": tool.get("result"),
        })
    return cleaned


def gateway_tools() -> list[dict[str, Any]]:
    return [
        {
            "name": "catalog_list",
            "description": "List backend tools with short descriptions. Use this instead of loading every schema.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        },
        {
            "name": "catalog_search",
            "description": "Search backend tools by name or description keyword.",
            "inputSchema": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        },
        {
            "name": "tool_schema",
            "description": "Return the full input schema for one backend tool.",
            "inputSchema": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
        {
            "name": "invoke",
            "description": "Call a backend tool by name with a JSON arguments object.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "arguments": {"type": "object"},
                },
                "required": ["name"],
            },
        },
    ]


class Catalog:
    def __init__(self, tools: list[dict[str, Any]]):
        self.tools = {t["name"]: t for t in tools}

    def list(self) -> list[dict[str, str]]:
        rows = []
        for name, tool in self.tools.items():
            desc = tool["description"]
            if len(desc) > 160:
                desc = desc[:157] + "..."
            rows.append({"name": name, "description": desc})
        return rows

    def search(self, query: str) -> list[dict[str, str]]:
        q = query.lower()
        return [row for row in self.list() if q in row["name"].lower() or q in row["description"].lower()]

    def schema(self, name: str) -> dict[str, Any]:
        tool = self.tools.get(name)
        if not tool:
            raise KeyError(name)
        return {"name": tool["name"], "description": tool["description"], "inputSchema": tool["inputSchema"]}

    def invoke(self, name: str, arguments: dict[str, Any] | None) -> Any:
        tool = self.tools.get(name)
        if not tool:
            raise KeyError(name)
        if tool.get("result") is not None:
            return tool["result"]
        return {"ok": True, "tool": name, "arguments": arguments or {}}


def handle_call(catalog: Catalog, name: str, arguments: dict[str, Any] | None) -> tuple[Any, bool]:
    arguments = arguments or {}
    try:
        if name == "catalog_list":
            return catalog.list(), False
        if name == "catalog_search":
            if "query" not in arguments:
                return "missing query", True
            return catalog.search(str(arguments["query"])), False
        if name == "tool_schema":
            if "name" not in arguments:
                return "missing name", True
            return catalog.schema(str(arguments["name"])), False
        if name == "invoke":
            if "name" not in arguments:
                return "missing name", True
            return catalog.invoke(str(arguments["name"]), arguments.get("arguments") or {}), False
        return f"unknown tool: {name}", True
    except KeyError as exc:
        return f"unknown backend tool: {exc}", True


def mcp_response(msg_id: Any, result: Any = None, error: dict | None = None) -> dict[str, Any]:
    body: dict[str, Any] = {"jsonrpc": "2.0", "id": msg_id}
    if error is not None:
        body["error"] = error
    else:
        body["result"] = result
    return body


def dispatch(catalog: Catalog, message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    msg_id = message.get("id")
    params = message.get("params") or {}
    if method == "initialize":
        return mcp_response(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mcplazy", "version": __version__},
        })
    if method in {"notifications/initialized", "initialized"}:
        return None
    if method == "tools/list":
        return mcp_response(msg_id, {"tools": gateway_tools()})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        data, is_error = handle_call(catalog, name, arguments)
        text = data if isinstance(data, str) else json.dumps(data)
        return mcp_response(msg_id, {"content": [{"type": "text", "text": text}], "isError": is_error})
    if method == "ping":
        return mcp_response(msg_id, {})
    if msg_id is None:
        return None
    return mcp_response(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def read_message(stream) -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = stream.readline()
        if line == "":
            return None
        if isinstance(line, bytes):
            line = line.decode("utf-8")
        if line in ("\r\n", "\n"):
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    body = stream.read(length)
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    if not body:
        return None
    return json.loads(body)


def write_message(stream, message: dict[str, Any]) -> None:
    raw = json.dumps(message, separators=(",", ":")).encode("utf-8")
    stream.write(f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8"))
    stream.write(raw)
    stream.flush()


def tax_compare(catalog: Catalog) -> dict[str, Any]:
    dumped = json.dumps([
        {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
        for t in catalog.tools.values()
    ], separators=(",", ":"))
    lazy = json.dumps(gateway_tools(), separators=(",", ":"))
    return {
        "backend_tools": len(catalog.tools),
        "eager_tokens": estimate_tokens(dumped),
        "lazy_tokens": estimate_tokens(lazy),
        "saved_tokens": estimate_tokens(dumped) - estimate_tokens(lazy),
        "estimator": "ceil(utf8_bytes / 4)",
    }


def cmd_serve(catalog: Catalog) -> int:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        try:
            message = read_message(stdin)
        except (json.JSONDecodeError, ValueError, KeyError) as exc:
            write_message(stdout, mcp_response(None, error={"code": -32700, "message": str(exc)}))
            continue
        if message is None:
            return 0
        reply = dispatch(catalog, message)
        if reply is not None:
            write_message(stdout, reply)


def cmd_call(catalog: Catalog, tool: str, arguments: dict[str, Any]) -> int:
    data, is_error = handle_call(catalog, tool, arguments)
    if isinstance(data, str):
        print(data)
    else:
        print(json.dumps(data, indent=2))
    return 1 if is_error else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mcplazy",
        description="Lazy MCP gateway that loads tool schemas on demand.",
    )
    parser.add_argument("--catalog", required=True, help="JSON file of backend tools")
    parser.add_argument("--version", action="version", version=f"mcplazy {__version__}")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("serve", help="run as a stdio MCP server (default)")
    sub.add_parser("tax", help="compare eager schema tokens vs the four gateway tools")
    p_call = sub.add_parser("call", help="call a gateway tool from the CLI (for tests and demos)")
    p_call.add_argument("tool")
    p_call.add_argument("--args", default="{}", help="JSON object of arguments")
    args = parser.parse_args(argv)
    catalog = Catalog(load_catalog(Path(args.catalog)))
    cmd = args.cmd or "serve"
    if cmd == "tax":
        print(json.dumps(tax_compare(catalog), indent=2))
        return 0
    if cmd == "call":
        try:
            arguments = json.loads(args.args)
        except json.JSONDecodeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return cmd_call(catalog, args.tool, arguments)
    return cmd_serve(catalog)


if __name__ == "__main__":
    raise SystemExit(main())
