# libspec

A schema system for documenting Python library interfaces, tracking development maturity, and navigating what to build next.

## Overview

libspec provides a structured, machine-readable format for describing Python libraries. Unlike documentation generators that extract from code, libspec lets you **specify intent first**—what your library should be—then track progress toward that specification.

```bash
pip install libspec[cli]
```

**Core capabilities:**

- **Specify** types, functions, features, and their contracts
- **Track** development maturity from idea through release
- **Navigate** what's ready to implement, what's blocked, and why
- **Validate** specs with 40+ semantic lint rules
- **Extend** with domain-specific semantics (async, web, data, etc.)

## Quick Example

```json
{
  "$schema": "libspec/1.0",
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "types": [{
      "name": "Client",
      "kind": "class",
      "module": "mylib",
      "docstring": "HTTP client with connection pooling",
      "maturity": "implemented",
      "requires": [
        {"ref": "#/types/ConnectionPool", "min_maturity": "tested"}
      ],
      "methods": [
        {"name": "get", "signature": "(self, url: str) -> Response"}
      ]
    }]
  }
}
```

---

## CLI: Query & Navigate Your Spec

All commands output JSON by default—pipe to `jq` for extraction. Use `--text` for compact output.

### Workflow Examples

```bash
# Quick health check
libspec info                          # Overview: counts, coverage, extensions

# Find what needs work
libspec types --undocumented          # Missing docstrings
libspec navigate gaps                 # Missing signatures, tests, evidence

# Development navigation
libspec next                          # What's ready to advance?
libspec blocked                       # What's stuck and why?
libspec blocked --by-requirement      # Group by blocking cause

# Architecture visualization
libspec modules --tree --entities     # Hierarchical view with types/functions
libspec deps --format mermaid         # Export dependency graph

# CI validation
libspec validate --strict && libspec lint --strict
```

### Command Categories

| Category | Commands | Purpose |
|----------|----------|---------|
| **Inspect** | `info`, `types`, `functions`, `features`, `modules` | Browse spec contents |
| **Query** | `query`, `refs`, `search` | Custom jq queries, resolve references |
| **Validate** | `validate`, `lint` | Schema validation, semantic linting |
| **Analyze** | `coverage`, `deps`, `surface` | Coverage gaps, dependencies, API surface |
| **Navigate** | `next`, `blocked`, `gaps`, `progress` | Development workflow |

---

## Maturity Tracking

Every entity can have a `maturity` field tracking its development stage:

```
idea → specified → designed → implemented → tested → documented → released → deprecated
```

### Requirements & Dependencies

The `requires` field declares dependencies with optional maturity constraints:

```json
{
  "name": "WebSocketHandler",
  "maturity": "designed",
  "requires": [
    {"ref": "#/types/Connection", "min_maturity": "implemented"},
    {"ref": "#/types/MessageCodec", "min_maturity": "tested", "reason": "Need stable codec API"}
  ]
}
```

This enables:
- **`libspec blocked`** — See what's waiting on dependencies
- **`libspec next`** — See what's ready to advance
- **Lint rule X004** — Detect circular dependencies
- **Lint rule X005** — Flag unsatisfied requirements

### Lifecycle Extension (Optional)

For teams needing auditable workflows, the `lifecycle` extension adds **gates** and **evidence**:

```
┌─────────────────────────────────────────────────────┐
│  Lifecycle Extension (opt-in)                        │
│  • Gates: required evidence per transition           │
│  • Evidence: PRs, tests, docs, approvals            │
│  → "Can this advance? What's missing?"              │
├─────────────────────────────────────────────────────┤
│  Core Maturity (always available)                    │
│  • 8-level progression                              │
│  • Requirements with min_maturity                   │
│  → "How developed is this?"                         │
└─────────────────────────────────────────────────────┘
```

```json
{
  "extensions": ["lifecycle"],
  "library": {
    "default_workflow": "standard",
    "workflows": [{
      "name": "standard",
      "maturity_gates": [
        {"from_maturity": "implemented", "to_maturity": "tested",
         "gates": [{"type": "tests_passing", "required": true}]}
      ]
    }]
  }
}
```

---

## Extensions

Extensions add optional, domain-specific fields to core entities. Enable them in your spec:

```json
{"extensions": ["async", "errors", "web"]}
```

### Domain Extensions

Model specific technical domains:

| Extension | Purpose | Key Additions |
|-----------|---------|---------------|
| `async` | Async/concurrent systems | Lifecycle states, cancellation, sync primitives |
| `web` | Web frameworks | Routes, middleware, dependencies |
| `data` | Data processing | Transforms, dtypes, lazy evaluation |
| `cli` | Command-line tools | Commands, arguments, options, exit codes |
| `orm` | Database ORMs | Models, relationships, migrations |
| `events` | Event-driven systems | Events, handlers, sagas |
| `state` | State machines | States, transitions, guards |
| `testing` | Test frameworks | Fixtures, markers, factories |
| `plugins` | Extensible systems | Extension points, hooks, registries |
| `config` | Configuration | Settings, sources, profiles, secrets |
| `serialization` | Serialization | Formats, encoders, type mappings |

### Concern Extensions

Cross-cutting aspects for any library:

| Extension | Purpose | Key Additions |
|-----------|---------|---------------|
| `errors` | Error handling | Exception hierarchy, error codes, recovery |
| `perf` | Performance | Complexity, benchmarks, scaling |
| `safety` | Safety guarantees | Thread safety, reentrancy, memory |
| `versioning` | API evolution | Deprecations, breaking changes, migrations |
| `observability` | Debugging | Logging, metrics, tracing, health checks |
| `lifecycle` | Development workflow | Gates, evidence, workflow definitions |

### Compatibility

All extensions compose freely. Recommended combinations:

- **Web APIs**: `async` + `errors` + `web` + `observability`
- **Data Processing**: `data` + `serialization` + `perf`
- **CLI Tools**: `cli` + `config` + `errors`
- **Plugin Systems**: `plugins` + `lifecycle` + `versioning`

---

## Pydantic-First Architecture

libspec uses Pydantic models as the **single source of truth**. JSON schemas are generated artifacts, never edited directly.

### Key Types

Models use 30+ constrained types with pattern validation:

| Type | Pattern | Example |
|------|---------|---------|
| `KebabCaseId` | `^[a-z][a-z0-9]*(-[a-z0-9]+)*$` | `user-auth`, `retry-logic` |
| `PascalCaseName` | `^[A-Z][a-zA-Z0-9]*$` | `Connection`, `HttpClient` |
| `CrossReference` | `#/types/X`, `lib#/functions/Y` | `#/types/Handler/methods/run` |
| `EntityMaturity` | enum | `idea`, `implemented`, `released` |

### Strict Mode

Enable strict validation for production specs:

```bash
libspec --strict-models validate
```

Or in `pyproject.toml`:

```toml
[tool.libspec]
strict_models = true
```

Strict mode adds: type coercion rejection, duplicate detection, bounded numeric validation, and path existence checks.

### Development

```bash
uv run python tools/generate_schema.py        # Regenerate schemas from models
uv run python tools/generate_schema.py --check  # CI: verify schemas are current
```

---

## Core Schema

| Entity | Purpose |
|--------|---------|
| **Library** | Root container: name, version, tagline |
| **Module** | Package structure, exports, dependencies |
| **TypeDef** | Classes, protocols, enums, dataclasses, type aliases |
| **FunctionDef** | Functions, decorators, context managers |
| **Feature** | Behavioral specifications with test steps |
| **Principle** | Design philosophy, rationale, anti-patterns |

### Cross-References

Link entities within or across specs:

```
#/types/Connection                    # Type in same spec
#/types/Connection/methods/send       # Method on type
#/functions/spawn                     # Function
#/features/retry-on-failure           # Feature
otherlib#/types/Client                # Type in another spec
```

---

## Documentation

- [Core Schema Reference](docs/core.md) — Types, functions, features, maturity, requirements
- [CLI Reference](docs/cli.md) — All commands, options, lint rules
- [Extensions Reference](docs/extensions.md) — Domain and concern extensions
- [Lifecycle Extension](docs/lifecycle.md) — Workflows, gates, evidence
- [Examples](docs/examples/) — Sample specifications

## License

MIT
