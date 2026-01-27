# docling-metrics

Monorepo for Docling metric packages — types, evaluators, and scoring utilities for document processing evaluation.

## Packages

| Package | Description |
|---------|-------------|
| [docling-metric-types](packages/docling-metric-types/) | Base metric types and abstract interfaces |

## Development

This repository uses [uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/). All packages are developed in a single virtual environment with compatible dependencies.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install all packages (editable) + dev tools
uv sync

# Run tests for a specific package
uv run pytest packages/docling-metric-types/tests

# Run all tests
uv run pytest packages/*/tests

# Run linting and formatting
pre-commit run --all-files
```

Changes to any workspace package are immediately available to all other packages in the same environment — no reinstall needed.

## Adding a New Package

1. Create `packages/<package-name>/` with a `pyproject.toml`, source directory, and `tests/`
2. If it depends on another workspace package, add it to `[project] dependencies` and declare `[tool.uv.sources]`:
   ```toml
   [project]
   dependencies = ["docling-metric-types"]

   [tool.uv.sources]
   docling-metric-types = { workspace = true }
   ```
3. Run `uv sync` to regenerate the lock file

## License

MIT
