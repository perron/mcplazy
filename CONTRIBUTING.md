# Contributing to mcplazy

Thanks for wanting to help. This is a small, original, clean-room CLI. The useful work is tight tests and honest docs, not a larger surface area.

## How to run tests

Python 3.10 or later.

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest -q
```

Please run the test suite before you open a pull request, and add a test for any new behavior.

## Good first issues

These are useful and bounded:

- Optional live stdio forwarding for `invoke`, covered by tests (this release uses a static catalog on purpose).
- Add a `limit` argument to `catalog_list` and `catalog_search`.
- Reject or warn on a catalog tool whose `inputSchema` is not an object.

If you pick one, open an issue first so two people do not do the same work.

## Pull request guidelines

- Keep the change small and explain why it is needed.
- Do not add a required runtime dependency without a strong reason. This tool has none today.
- Do not copy source from another project. Original code only.
- Do not weaken a safety check to make a test easier.
- Update the README if the user-visible behavior or limits change. Keep the claims honest.
- Do not commit secrets, store files, journals, or `.env` files.

## Reporting a vulnerability

See [SECURITY.md](SECURITY.md). Do not open a public issue that includes secrets or a live exploit payload.
