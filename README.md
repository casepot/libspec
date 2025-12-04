# libspec

A schema system for documenting library interfaces, architecture, and behavioral specifications.

## Overview

libspec provides a structured, machine-readable format for describing Python libraries. It enables:

- **Systematic querying** of interfaces (types, functions, methods)
- **Machine validation** of specification files
- **Behavioral specifications** linked to testable assertions
- **Development tracking** with maturity levels and dependency requirements
- **Navigation commands** to find what's ready, blocked, or has gaps
- **Domain-specific extensions** for async, web, data, CLI, and more
- **Cross-cutting concern extensions** for errors, performance, safety, etc.

## Quick Start

```bash
pip install libspec
```

Create a `specs/libspec.json` in your library:

```json
{
  "$schema": "libspec/1.0",
  "extensions": ["async", "errors"],
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "tagline": "A library that does things",
    "types": [
      {
        "name": "MyClass",
        "kind": "class",
        "module": "mylib.core",
        "docstring": "A class that represents something",
        "methods": [
          {
            "name": "do_something",
            "signature": "(self, x: int) -> str",
            "description": "Does something with x"
          }
        ]
      }
    ]
  }
}
```

Validate your spec:

```python
from libspec import validate_spec

errors = validate_spec("specs/libspec.json")
if errors:
    for e in errors:
        print(f"Error: {e}")
```

## Development Notes

- **Pydantic-first**: Models live in `src/libspec/models/`; JSON Schemas are generated artifacts. Regenerate the core schema from models with `uv run python tools/generate_schema.py` (use `--check` in CI). Regenerate extension models from extension schemas with `uv run python tools/generate_models.py` (auto-renames `async.py` → `async_.py`); drift check via `uv run python tools/check_generated.py`.
- **Strict parsing**: `--strict-models` (or `[tool.libspec].strict_models = true`) enables strict validation: extension-field gating, duplicate detection, non-coercive booleans on risky flags, bounded ints/decimals for timeouts/status codes/rate limits/benchmarks, and path checks (lifecycle evidence, coverage targets, config/discovery/migration locations).

## Schema Structure

### Core Schema

The core schema captures universal library concepts:

- **Library**: Root container with name, version, description
- **Principles**: Design philosophy and anti-patterns
- **Modules**: Package structure and dependencies
- **Types**: Classes, protocols, enums, dataclasses, type aliases
- **Functions**: Functions, decorators, context managers
- **Features**: Behavioral specifications with test steps
- **Maturity**: Development stage tracking (idea → specified → designed → implemented → tested → documented → released)
- **Requirements**: Dependency tracking with optional maturity constraints

### Domain Extensions

Extensions add domain-specific semantics:

| Extension | Domain | Key Additions |
|-----------|--------|---------------|
| `async` | Async/concurrent systems | Lifecycle, cancellation, sync primitives |
| `web` | Web frameworks | Routes, middleware, request/response |
| `data` | Data processing | Transforms, dtypes, lazy eval |
| `cli` | Command-line tools | Commands, arguments, options |
| `orm` | Database ORMs | Models, relationships, queries |
| `testing` | Test frameworks | Fixtures, markers, hooks |
| `events` | Event-driven systems | Publishers, subscribers, topics |
| `state` | State machines | States, transitions, guards |
| `plugins` | Extensible systems | Extension points, hooks |

### Concern Extensions

Cross-cutting aspects applicable to any library:

| Extension | Concern | Key Additions |
|-----------|---------|---------------|
| `errors` | Error taxonomy | Exception hierarchy, error codes |
| `perf` | Performance | Complexity, benchmarks, scaling |
| `safety` | Safety guarantees | Thread safety, reentrancy |
| `config` | Configuration | Settings, env vars, profiles |
| `versioning` | API evolution | Deprecations, migrations |
| `observability` | Debugging | Logging, metrics, tracing |
| `lifecycle` | API maturity | Workflows, states, transitions, evidence |

## Cross-References

Reference other entities within or across specs:

```
Internal:   #/types/Handle
            #/types/Handle/methods/send
            #/functions/spawn
            #/features/ACTOR_001

External:   other_lib#/types/SomeType
```

## Navigation Commands

The CLI provides navigation commands for development workflow:

```bash
libspec next                  # What's ready to advance?
libspec blocked               # What's stuck and why?
libspec blocked --by-requirement  # Group by what's blocking
libspec navigate gaps         # What's missing docstrings/tests?
libspec navigate progress     # Dashboard of maturity distribution
```

These commands work with the core `maturity` field. Enable the `lifecycle` extension to add workflow gates and evidence requirements for transitions.

## Documentation

- [Core Schema Reference](docs/core.md) - Types, functions, features, maturity, requirements
- [Extensions Reference](docs/extensions.md) - Domain and concern extensions
- [Lifecycle Extension](docs/lifecycle.md) - Workflow gates and evidence
- [CLI Reference](docs/cli.md) - Commands, validation, linting, navigation
- [Examples](docs/examples/) - Sample specifications

## License

MIT
