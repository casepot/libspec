# Repository Guidelines

This guide is for contributors working on libspec. Keep changes small, typed, and validated by the commands below to stay consistent with the existing code and schema conventions.

## Project Structure & Module Organization
- `src/libspec/` – typed package; `__init__.py` exposes schema helpers. CLI lives in `cli/`, schemas in `schema/`, lint rules in `cli/lint/`.
- `src/libspec/cli/` – Click entry (`app.py`), command groups in `commands/`, shared config/output helpers, lint rule registry.
- `src/libspec/schema/` – JSON Schema definitions (`core.schema.json` plus domain/concern extensions). Keep IDs stable when editing.
- `docs/` – user-facing docs and examples (`docs/examples/minimal.json` is a good test fixture). `CLAUDE.md` has extra dev notes.
- `pyproject.toml` – packaging plus ruff/mypy settings; `uv.lock` pins dependencies; `tools/` reserved for helper scripts.

## Build, Test, and Development Commands
- `uv sync` – install project and dev deps into `.venv`.
- `uv run libspec --help` or `uv run libspec inspect specs/libspec.json --text` – run the CLI locally.
- `uv run ruff check src/` (add `--fix` for safe autofixes) – lint and import-sort; target line length is 100.
- `uv run mypy src/` – strict type checking.
- `uv run pytest` – run tests (currently none); use `uv run pytest --cov=src/libspec` when adding coverage.
- `uv build` – build wheel/sdist; `uv publish` – release to PyPI (requires credentials).

## Coding Style & Naming Conventions
- Python 3.10+, 4-space indent, prefer f-strings, avoid `Any` where possible; keep functions small and pure when feasible.
- Naming: modules/files `snake_case`; classes `PascalCase`; functions/vars `snake_case`; CLI command names mirror files in `cli/commands/`.
- JSON schemas use camelCase keys; keep `$schema` refs and `$id` consistent and documented.
- Run ruff before committing; no auto-formatter mandated—follow ruff and mypy guidance to align style.

## Testing Guidelines
- Framework: pytest. Place tests under `tests/` mirroring package paths (e.g., `tests/cli/test_inspect.py`).
- Use `docs/examples/minimal.json` or small fixtures under `tests/fixtures/` to exercise schema/CLI paths.
- Prefer text-mode CLI output for assertions; keep outputs deterministic and stable across Python versions.
- Add coverage for new lint rules, schema validations, and CLI flags; avoid over-mocking and assert on user-visible behavior.

## Commit & Pull Request Guidelines
- Commit messages: short, imperative summaries (e.g., `Add coverage command`, `Fix lint error`). Keep unrelated changes split into separate commits.
- Before pushing: run `uv run ruff check src/`, `uv run mypy src/`, and `uv run pytest`.
- PRs should explain what/why, note schema or CLI-breaking changes, include test evidence, and link issues. Add screenshots only when output formatting changes.
- Update docs/examples when schemas or CLI flags change; mention any new config keys introduced.
