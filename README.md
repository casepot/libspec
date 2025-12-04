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

A minimal spec defining one type with a dependency:

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

## Core Schema

A libspec file describes your library through six entity types:

```
Library (root)
├── modules[]      → Package structure and exports
├── types[]        → Classes, protocols, enums, type aliases
├── functions[]    → Standalone functions and decorators
├── features[]     → Behavioral specifications
└── principles[]   → Design philosophy
```

### Entity Types

| Entity | Role | Key Fields |
|--------|------|------------|
| **TypeDef** | Describes classes, protocols, enums, dataclasses, and type aliases. The primary building blocks of your API surface. | `name`, `kind`, `module`, `methods[]`, `properties[]`, `generic_params[]` |
| **FunctionDef** | Describes standalone functions, decorators, context managers, and generators. Captures signatures, exceptions, and behavior. | `name`, `kind`, `signature`, `module`, `raises[]`, `returns` |
| **Feature** | Behavioral specifications that cut across types and functions. Useful for documenting capabilities, acceptance criteria, and test scenarios. | `id`, `category`, `summary`, `steps[]`, `references[]` |
| **Module** | Maps your package structure. Declares what each module exports and its dependencies on other modules. | `path`, `exports[]`, `depends_on[]`, `internal` |
| **Principle** | Captures design philosophy and rationale. Documents the "why" behind architectural decisions and anti-patterns to avoid. | `id`, `title`, `rationale`, `anti_patterns[]` |

**TypeDef kinds**: `class`, `protocol`, `enum`, `dataclass`, `namedtuple`, `typeddict`, `type_alias`, `abc`

**FunctionDef kinds**: `function`, `decorator`, `context_manager`, `generator`, `async_generator`

### Cross-References

Entities reference each other using `#/` paths—in `requires` fields for dependencies, `references` for documentation links, and anywhere you need to connect parts of your spec. The syntax follows JSON Pointer style:

- `#/types/Name` — reference a type
- `#/functions/name` — reference a function
- `#/features/feature-id` — reference a feature
- `#/types/Name/methods/method` — reference a method on a type
- `otherlib#/types/Name` — reference into another spec

Lint rule X001 validates that all references resolve to existing entities.

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

Every entity can have a `maturity` field tracking its development stage. The eight levels in order:

`idea` → `specified` → `designed` → `implemented` → `tested` → `documented` → `released` → `deprecated`

### Requirements & Dependencies

The `requires` field declares dependencies with optional maturity constraints. For example, a type that depends on other types being at certain maturity levels:

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

Model specific technical domains. Each extension adds new fields to core entities:

| Extension | Purpose | Fields Added |
|-----------|---------|--------------|
| `async` | Async/concurrent systems | `async_lifecycle`, `cancellation_safe`, `sync_primitives` |
| `web` | Web frameworks | `routes[]`, `middleware[]`, `dependencies[]` |
| `data` | Data processing | `transforms[]`, `dtype`, `lazy` |
| `cli` | Command-line tools | `commands[]`, `arguments[]`, `exit_codes[]` |
| `orm` | Database ORMs | `table`, `relationships[]`, `migrations[]` |
| `events` | Event-driven systems | `events[]`, `handlers[]`, `sagas[]` |
| `state` | State machines | `states[]`, `transitions[]`, `guards[]` |
| `testing` | Test frameworks | `fixtures[]`, `markers[]`, `factories[]` |
| `plugins` | Extensible systems | `extension_points[]`, `hooks[]`, `registry` |
| `config` | Configuration | `settings[]`, `sources[]`, `profiles[]` |
| `serialization` | Serialization | `formats[]`, `encoders[]`, `type_mappings[]` |

### Concern Extensions

Cross-cutting aspects that apply to any library:

| Extension | Purpose | Fields Added |
|-----------|---------|--------------|
| `errors` | Error handling | `error_codes[]`, `recovery_strategies[]`, `exception_hierarchy` |
| `perf` | Performance | `complexity`, `benchmarks[]`, `scaling` |
| `safety` | Safety guarantees | `thread_safe`, `reentrant`, `memory_safety` |
| `versioning` | API evolution | `deprecated_in`, `removed_in`, `migration_guide` |
| `observability` | Debugging | `logs[]`, `metrics[]`, `traces[]`, `health_checks[]` |
| `lifecycle` | Development workflow | `workflows[]`, `maturity_gates[]`, `maturity_evidence[]` |

### Compatibility

All extensions compose freely. Recommended combinations:

- **Web APIs**: `async` + `errors` + `web` + `observability`
- **Data Processing**: `data` + `serialization` + `perf`
- **CLI Tools**: `cli` + `config` + `errors`
- **Plugin Systems**: `plugins` + `lifecycle` + `versioning`

---

## Pydantic-First Architecture

libspec uses Pydantic models as the **single source of truth**. JSON schemas are generated artifacts, never edited directly. Models use 30+ constrained types with pattern validation to enforce naming conventions and reference formats.

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

### For Contributors

If you're modifying libspec's Pydantic models, regenerate the JSON schemas:

```bash
uv run python tools/generate_schema.py        # Regenerate schemas from models
uv run python tools/generate_schema.py --check  # CI: verify schemas match models
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
