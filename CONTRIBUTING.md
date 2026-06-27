# Contributing

Thanks for helping improve the PayHub Python SDK.

## Development setup

We use [uv](https://docs.astral.sh/uv/). Install the dev tools into a managed
environment:

```bash
uv sync --extra dev
```

## Checks (must pass before opening a PR)

```bash
uv run ruff check .      # lint
uv run mypy src          # static typing (strict)
uv run pytest            # tests
```

CI runs all three on Python 3.9, 3.10, 3.11 and 3.12.

## Scope & conventions

- The SDK mirrors the PayHub OpenAPI spec — keep the public surface in sync with
  the API. Prefer small, typed additions.
- **No runtime dependencies**: stick to the standard library so the SDK stays
  trivial to embed anywhere.
- Open an issue first for larger changes so we can align on the design.
- Add or update tests with every behaviour change; never call the live API from
  tests (use the injectable `Transport`).
