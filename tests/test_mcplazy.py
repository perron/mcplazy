import io
import json
from pathlib import Path
import pytest
import mcplazy.cli as ml


def catalog_file(tmp_path: Path) -> Path:
    tools = {
        "tools": [
            {
                "name": "github.create_issue",
                "description": "Create an issue in a GitHub repository.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "body": {"type": "string"}},
                    "required": ["title"],
                },
                "result": {"number": 42},
            },
            {
                "name": "slack.post_message",
                "description": "Post a message to a Slack channel.",
                "inputSchema": {"type": "object", "properties": {"channel": {"type": "string"}, "text": {"type": "string"}}},
                "result": {"ok": True},
            },
        ]
    }
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps(tools))
    return path


def test_help_and_version(tmp_path):
    # --help/--version are parsed after --catalog is required? Check argparse order.
    # --version is on the parent parser, so it should work even without --catalog
    # because action=version exits during parse. Same for --help.
    with pytest.raises(SystemExit) as exc:
        ml.main(["--help"])
    assert exc.value.code == 0
    with pytest.raises(SystemExit) as exc:
        ml.main(["--version"])
    assert exc.value.code == 0


def test_catalog_list_and_search(tmp_path, capsys):
    path = catalog_file(tmp_path)
    assert ml.main(["--catalog", str(path), "call", "catalog_list"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {r["name"] for r in rows} == {"github.create_issue", "slack.post_message"}
    assert ml.main(["--catalog", str(path), "call", "catalog_search", "--args", json.dumps({"query": "slack"})]) == 0
    found = json.loads(capsys.readouterr().out)
    assert found == [{"name": "slack.post_message", "description": "Post a message to a Slack channel."}]


def test_schema_and_invoke(tmp_path, capsys):
    path = catalog_file(tmp_path)
    assert ml.main(["--catalog", str(path), "call", "tool_schema", "--args", json.dumps({"name": "github.create_issue"})]) == 0
    schema = json.loads(capsys.readouterr().out)
    assert "inputSchema" in schema
    assert ml.main(["--catalog", str(path), "call", "invoke", "--args", json.dumps({"name": "github.create_issue", "arguments": {"title": "Bug"}})]) == 0
    assert json.loads(capsys.readouterr().out) == {"number": 42}


def test_invoke_without_canned_result_is_not_live(tmp_path, capsys):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({
        "tools": [{"name": "live.tool", "description": "Would talk to a backend if forwarding existed.", "inputSchema": {"type": "object"}}]
    }))
    assert ml.main(["--catalog", str(path), "call", "invoke", "--args", json.dumps({"name": "live.tool", "arguments": {"x": 1}})]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data == {"ok": True, "tool": "live.tool", "arguments": {"x": 1}}


def test_tax_saves_tokens(tmp_path, capsys):
    path = catalog_file(tmp_path)
    assert ml.main(["--catalog", str(path), "tax"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["backend_tools"] == 2
    assert data["eager_tokens"] > 0
    assert data["saved_tokens"] == data["eager_tokens"] - data["lazy_tokens"]


def test_tax_saves_tokens_on_large_catalog(tmp_path, capsys):
    tools = []
    for i in range(40):
        tools.append({
            "name": f"server.tool_{i}",
            "description": "A detailed tool description that would otherwise be injected on every turn, including parameter notes and examples.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "resource id"},
                    "limit": {"type": "integer", "description": "max rows to return from the query"},
                    "q": {"type": "string", "description": "search query"},
                },
            },
        })
    path = tmp_path / "big.json"
    path.write_text(json.dumps({"tools": tools}))
    assert ml.main(["--catalog", str(path), "tax"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["saved_tokens"] > 0
    assert data["lazy_tokens"] < data["eager_tokens"]


def test_dispatch_initialize_and_tools_list(tmp_path):
    path = catalog_file(tmp_path)
    catalog = ml.Catalog(ml.load_catalog(path))
    init = ml.dispatch(catalog, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init["result"]["serverInfo"]["name"] == "mcplazy"
    listed = ml.dispatch(catalog, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    names = [t["name"] for t in listed["result"]["tools"]]
    assert names == ["catalog_list", "catalog_search", "tool_schema", "invoke"]
    called = ml.dispatch(catalog, {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "catalog_search", "arguments": {"query": "issue"}},
    })
    assert called["result"]["isError"] is False
    assert "github.create_issue" in called["result"]["content"][0]["text"]


def test_missing_catalog(tmp_path, capsys):
    assert ml.main(["--catalog", str(tmp_path / "nope.json"), "tax"]) == 1
    assert "error:" in capsys.readouterr().err


def test_bad_json_catalog(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text("{nope")
    assert ml.main(["--catalog", str(path), "tax"]) == 1
    assert "error:" in capsys.readouterr().err


def test_duplicate_tool_names(tmp_path, capsys):
    path = tmp_path / "dup.json"
    path.write_text(json.dumps({"tools": [{"name": "a"}, {"name": "a"}]}))
    assert ml.main(["--catalog", str(path), "tax"]) == 1
    assert "duplicate tool name" in capsys.readouterr().err


def test_unknown_and_missing_args(tmp_path, capsys):
    path = catalog_file(tmp_path)
    assert ml.main(["--catalog", str(path), "call", "catalog_search", "--args", "{}"]) == 1
    assert "missing query" in capsys.readouterr().out
    assert ml.main(["--catalog", str(path), "call", "invoke", "--args", json.dumps({"name": "no.such"})]) == 1
    assert "unknown backend tool" in capsys.readouterr().out


def test_stdio_framing(tmp_path):
    catalog = ml.Catalog(ml.load_catalog(catalog_file(tmp_path)))
    msg = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
    raw = json.dumps(msg).encode("utf-8")
    buf_in = io.BytesIO(f"Content-Length: {len(raw)}\r\n\r\n".encode("utf-8") + raw)
    message = ml.read_message(buf_in)
    assert message["method"] == "tools/list"
    reply = ml.dispatch(catalog, message)
    buf_out = io.BytesIO()
    ml.write_message(buf_out, reply)
    buf_out.seek(0)
    back = ml.read_message(buf_out)
    names = [t["name"] for t in back["result"]["tools"]]
    assert "catalog_list" in names


def test_dispatch_ping_and_unknown(tmp_path):
    catalog = ml.Catalog(ml.load_catalog(catalog_file(tmp_path)))
    ping = ml.dispatch(catalog, {"jsonrpc": "2.0", "id": 9, "method": "ping"})
    assert ping["result"] == {}
    notify = ml.dispatch(catalog, {"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert notify is None
    missing = ml.dispatch(catalog, {"jsonrpc": "2.0", "id": 10, "method": "no/such"})
    assert missing["error"]["code"] == -32601


def test_unicode_search(tmp_path, capsys):
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({
        "tools": [{"name": "notes.search", "description": "日本語のメモを検索します。", "inputSchema": {"type": "object"}}]
    }), encoding="utf-8")
    assert ml.main(["--catalog", str(path), "call", "catalog_search", "--args", json.dumps({"query": "メモ"}, ensure_ascii=False)]) == 0
    found = json.loads(capsys.readouterr().out)
    assert found[0]["name"] == "notes.search"


def test_empty_catalog_tax(tmp_path, capsys):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"tools": []}))
    assert ml.main(["--catalog", str(path), "tax"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["backend_tools"] == 0
    assert data["eager_tokens"] >= 1  # "[]" still has a token estimate
    assert data["lazy_tokens"] > 0


def test_invalid_content_length():
    buf = io.BytesIO(b"Content-Length: -1\r\n\r\n")
    with pytest.raises(ValueError):
        ml.read_message(buf)
    buf = io.BytesIO(b"Content-Length: nope\r\n\r\n")
    with pytest.raises(ValueError):
        ml.read_message(buf)
