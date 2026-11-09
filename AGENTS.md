# AGENTS.md

Instructions for coding agents (Claude Code, Codex, Cursor, Grok Bot, and similar) working in this repository.

## What this repo is

`mcplazy` is a small Python 3.10+ command-line tool to expose four catalog tools instead of dumping every backend schema. It has no required runtime dependencies and no API key. Layout:

- `mcplazy/cli.py` — the implementation and the `main()` entry point (exit code is an `int`)
- `mcplazy/__main__.py` — `python -m mcplazy`
- `mcplazy/__init__.py` — `__version__`
- `tests/test_mcplazy.py` — pytest suite
- `pyproject.toml` — packaging, the `mcplazy` script, and the `dev` extra (`pytest`)
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `PROOF.md` — human docs

mcplazy/cli.py is a static-catalog MCP gateway over stdio. invoke does not forward to a live backend in this release. tests/test_mcplazy.py covers catalog calls, framing, and tax math.

## How to run tests

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
mcplazy --help
mcplazy --version
```

`pip install .` in a fresh virtualenv must leave `mcplazy` on `PATH`.

## Conventions

- Keep changes small. Match the existing style: standard library, type hints, `argparse`, exit codes documented in the README.
- If you add behavior, add a test for it. Prefer tests of user-visible behavior over tests of internals.
- Do not add network calls, API keys, or telemetry.
- Do not copy source from other tools. This is a clean-room project.
- If a README, SECURITY.md, or Limits section would become untrue, update it in the same change.
- Do not commit secrets. For `mcplazy`, also do not commit local store/journal/database files (see `.gitignore`).
- Token estimates in this family of tools, when present, are `ceil(utf-8 bytes / 4)`. Do not describe them as a vendor tokenizer.

## If you are using the tool rather than changing it

Install it from this checkout or from `pip install git+https://github.com/perron/mcplazy.git`, then follow the 30-second quick start in the README. The README Limits section is the contract for what this release does and does not do.
