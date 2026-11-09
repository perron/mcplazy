# mcplazy

A tiny MCP gateway that exposes four tools — `catalog_list`, `catalog_search`,
`tool_schema`, and `invoke` — instead of dumping every backend tool schema
into the context window on every turn.

Point it at a JSON catalog of backend tools (a `tools/list` dump, or a
hand-written list). In serve mode it speaks MCP over stdio with
`Content-Length` framing.

## Install

```bash
python3 -m pip install -e .
```

## 30-second example

```bash
cat > catalog.json << 'EOF'
{
  "tools": [
    {
      "name": "github.create_issue",
      "description": "Create an issue in a GitHub repository.",
      "inputSchema": {"type": "object", "properties": {"title": {"type": "string"}}, "required": ["title"]},
      "result": {"number": 42}
    }
  ]
}
EOF

mcplazy --catalog catalog.json tax
mcplazy --catalog catalog.json call catalog_search --args '{"query":"issue"}'
```

`tax` prints eager vs lazy schema token estimates (`ceil(utf-8 bytes / 4)`).
`serve` is the stdio MCP server you can hook into a client later.

This first release uses a static catalog (and optional canned `result`
values) so it can be tested without live credentials. Forwarding to a live
stdio backend can be added next without changing the four gateway tools.

## Credit

Motivated by the MCP "context tax" reports of late Oct / early Nov 2026.
Original JSON-RPC implementation; no source was copied from any MCP server.
