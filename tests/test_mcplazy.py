import json
from pathlib import Path
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


def test_tax_saves_tokens(tmp_path, capsys):
    path = catalog_file(tmp_path)
    assert ml.main(["--catalog", str(path), "tax"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["backend_tools"] == 2
    assert data["eager_tokens"] > 0
    # With only two tiny tools the lazy gateway (4 tools) can be larger; grow the catalog.
    # The important assertion is that the function reports both numbers consistently.
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
