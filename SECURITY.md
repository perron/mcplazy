# Security Policy

This project is a small local command-line tool. It does not phone home and does not require an API key.

## Reporting a vulnerability

Please open a [GitHub issue](https://github.com/perron/mcplazy/issues) and mention that it is a security report. Do not include secrets, tokens, or private file contents in the issue.

If the report includes a working exploit against this tool, describe the impact and a minimal reproduction without pasting live credentials.

## Notes for this tool

mcplazy `serve` speaks MCP over stdio, not over the network. This release uses a static catalog (and optional canned results). It does not forward `invoke` to a live backend process. Treat a catalog file as untrusted input the same way you would any MCP tool list.

## Supported versions

The `master` branch and the latest tagged release, when one exists, are supported.
