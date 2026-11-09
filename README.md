# mcplazy

A tiny MCP gateway that exposes four tools — `catalog_list`, `catalog_search`,
`tool_schema`, and `invoke` — instead of dumping every backend tool schema
into the context window on every turn.

Point it at a JSON catalog of backend tools (a `tools/list` dump, or a
hand-written list). In serve mode it speaks MCP over stdio with
`Content-Length` framing.

## Install

Python 3.10 or later.

From a checkout:

```bash
python3 -m pip install .
python3 -m pip install -e ".[dev]"  # optional, for tests
```

## 30-second quick start

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

Sample output from that exact example:

```
$ mcplazy --catalog catalog.json tax
{
  "backend_tools": 1,
  "eager_tokens": 46,
  "lazy_tokens": 198,
  "saved_tokens": -152,
  "estimator": "ceil(utf8_bytes / 4)"
}

$ mcplazy --catalog catalog.json call catalog_search --args '{"query":"issue"}'
[
  {
    "name": "github.create_issue",
    "description": "Create an issue in a GitHub repository."
  }
]
```

With one tiny backend tool, the four gateway schemas can be *larger* than the eager dump (`saved_tokens` is negative). That is expected. On a 25-tool catalog the same command reports a savings (in one measured run: eager 2161, lazy 198, saved 1963, still `ceil(utf-8 bytes / 4)`).

`tax` prints eager vs lazy schema token estimates (`ceil(utf-8 bytes / 4)`).
`serve` is the stdio MCP server you can hook into a client later.

This first release uses a static catalog (and optional canned `result`
values) so it can be tested without live credentials. Forwarding to a live
stdio backend can be added next without changing the four gateway tools.

## Credit

Motivated by the MCP "context tax" reports of late Oct / early Nov 2026.
Original JSON-RPC implementation; no source was copied from any MCP server.

## Limits

- This release uses a static catalog. Optional canned `result` values can be included in the catalog for demos and tests.
- `invoke` does **not** forward calls to a live MCP backend. If a tool has no canned `result`, it returns `{"ok": true, "tool": "...", "arguments": {...}}`.
- `serve` speaks MCP over stdio with `Content-Length` framing. It is not a network server.
- Incoming stdio messages larger than 8 MiB are rejected.
- Duplicate tool names in a catalog are an error.

From GitHub you can also install with:

```bash
python3 -m pip install git+https://github.com/perron/mcplazy.git
```

This package is not published to PyPI.

## Use it with your agent

You can point a coding agent at this repository and ask it to use the tool, adapt it, or write a small tool in the same style. That works with Claude Code, Codex, Cursor, Grok Bot, and anything else that can clone a git repo and run a Python CLI.

A short prompt you can paste:

> Clone https://github.com/perron/mcplazy and read the README limits carefully. Using the catalog at ./catalog.json, show me the tax comparison and a catalog_search for 'issue'. Do not claim that invoke talks to a live backend; this release uses a static catalog.

If you want a new tool in this style, say so explicitly: one job, standard-library Python, pytest first, no API key, and an honest Limits section.

## Contributing / how you can help

Bug reports, tight tests, and small honest features are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to run the suite and for pull request guidelines.

Good first issues:

- Optional live stdio forwarding for `invoke`, covered by tests (this release uses a static catalog on purpose).
- Add a `limit` argument to `catalog_list` and `catalog_search`.
- Reject or warn on a catalog tool whose `inputSchema` is not an object.

If you are unsure whether an idea fits, open an issue before writing a large patch.

## License

MIT. See `LICENSE`. Please read `SECURITY.md` before filing a vulnerability report. Agents should also read `AGENTS.md`.
