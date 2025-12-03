# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
uv sync                                  # Install dependencies (creates .venv automatically)
uv run libspec                           # Run CLI
uv run pytest                            # Run tests
uv run ruff check src/                   # Lint (use --fix for auto-fixes)
uv run mypy src/                         # Type check
uv run python tools/generate_schema.py   # Regenerate JSON schemas from Pydantic models (use --check in CI)
```

Publishing:
```bash
uv build                      # Build wheel and sdist
uv publish                    # Publish to PyPI
```

## Architecture

### Pydantic-First Design

**IMPORTANT:** This project uses Pydantic models as the single source of truth. All schema work happens in Python/Pydantic:

- **Models** (`src/libspec/models/`) - Pydantic models define all types, validation, and constraints
- **JSON Schemas** (`src/libspec/schema/`) - Generated artifacts from Pydantic models via `tools/generate_schema.py`

**Never edit JSON schema files directly.** Always modify the Pydantic models and regenerate schemas.

### Models (`src/libspec/models/`)

- `core.py` - Core entity types (TypeDef, FunctionDef, Feature, Module, etc.)
- `types.py` - Enums and constrained string types
- `base.py` - Base model classes (LibspecModel, ExtensibleModel, ExtensionModel)
- `extensions/` - Extension models (async_, web, testing, errors, perf, etc.)

### Schema System (`src/libspec/schema/`)

JSON Schema definitions (generated from Pydantic models):
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
- CLI flag `--strict-models` (or `[tool.libspec].strict_models = true`) enables strict Pydantic parsing plus duplicate detection.

### Lint System (`src/libspec/cli/lint/`)

Rule-based linting with categories:
- `S` (structural): Missing descriptions, empty types
- `N` (naming): ID/name conventions
- `C` (completeness): Missing signatures, empty enums
- `X` (consistency): Dangling refs, duplicates
- `V` (version): Python version compatibility

`LintRule` base class in `base.py`. Rules in `rules/` subdirectory (structural.py, naming.py, completeness.py, consistency.py, version.py).

Configure in pyproject.toml under `[tool.libspec.lint]`.

## Output Formats

All CLI commands default to JSON with metadata envelope. Use `--text` for compact output, `--no-meta` to omit envelope.

## Multi-File Refactoring

For systematic changes across files, dispatch parallel subagents (one per file) with explicit targets from a plan:

```
Task: "Update web.py: MiddlewareSpec.type, DependencySpec.factory → FunctionReference | None"
Task: "Update cli.py: CommandSpec.handler → FunctionReference | None"
```

Avoid subagents for: cross-file dependencies (order matters), single-line fixes.
