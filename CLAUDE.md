# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
uv sync                       # Install dependencies (creates .venv automatically)
uv run libspec                # Run CLI
uv run pytest                 # Run tests (none exist yet)
uv run ruff check src/        # Lint (use --fix for auto-fixes)
uv run mypy src/              # Type check
```

Publishing:
```bash
uv build                      # Build wheel and sdist
uv publish                    # Publish to PyPI
```

## Architecture

### Schema System (`src/libspec/schema/`)

JSON Schema definitions for library documentation:
- `core.schema.json` - Base schema for library, types, functions, features, modules, principles
- `extensions/` - Domain extensions (async, web, data, cli, orm, testing, events, state, plugins) and concern extensions (errors, perf, safety, config, versioning, observability)

Core API in `src/libspec/__init__.py`: `get_schema_path()`, `validate_spec()`, `get_core_schema()`

### CLI (`src/libspec/cli/`)

Click-based CLI with command groups:
- **inspect**: `info`, `types`, `functions`, `features`, `modules`, `principles`
- **query**: `query` (jq expressions), `refs` (resolve cross-references), `search`
- **validate**: `validate` (JSON Schema), `lint` (semantic rules)
- **analyze**: `coverage`, `deps`, `surface`

Key files:
- `app.py` - CLI entry point, command registration, `Context` class
- `spec_loader.py` - Spec file loading and parsing
- `output.py` - JSON/text output formatting
- `config.py` - `[tool.libspec]` config loading from pyproject.toml
- `tools/generate_models.py` - Regenerates extension models from JSON Schema (auto-renames `async.py` → `async_.py`); `tools/check_generated.py` fails if drift is detected.
- CLI flag `--strict-models` (or `[tool.libspec].strict_models = true`) enables strict Pydantic parsing plus duplicate detection.

### Lint System (`src/libspec/cli/lint/`)

Rule-based linting with categories:
- `S` (structural): Missing descriptions, empty types
- `N` (naming): ID/name conventions
- `C` (completeness): Missing signatures, empty enums
- `X` (consistency): Dangling refs, duplicates

`LintRule` base class in `base.py`. Rules in `rules/` subdirectory (structural.py, naming.py, completeness.py, consistency.py).

Configure in pyproject.toml under `[tool.libspec.lint]`.

## Output Formats

All CLI commands default to JSON with metadata envelope. Use `--text` for compact output, `--no-meta` to omit envelope.
