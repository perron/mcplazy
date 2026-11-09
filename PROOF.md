# mcplazy proof

Captured 2026-11-09 13:26 PST.

Fresh-venv install: `pip install .` succeeded and `mcplazy --version` printed `mcplazy 0.1.1`.

Tests: 16 passed in 0.03s

## tax (eager schemas vs four gateway tools)
```
{
  "backend_tools": 25,
  "eager_tokens": 2161,
  "lazy_tokens": 198,
  "saved_tokens": 1963,
  "estimator": "ceil(utf8_bytes / 4)"
}
```

## catalog_search for github.tool_1
```
[
  {
    "name": "github.tool_1",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_10",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_11",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_12",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_13",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_14",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_15",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_16",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_17",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_18",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  },
  {
    "name": "github.tool_19",
    "description": "A detailed GitHub tool description that would otherwise be injected on every turn, including parameter notes and examples for issues, pulls, and comments."
  }
]
```

This release uses a static catalog. `invoke` does not forward to a live backend.
