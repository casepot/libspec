# Extension Compatibility Guide

This document describes how libspec extensions interact with each other and provides guidance on combining extensions effectively.

## Extension Categories

### Domain Extensions

Extensions that model specific technical domains:

| Extension | Purpose |
|-----------|---------|
| `async` | Async/concurrent semantics (lifecycle states, cancellation, scheduling) |
| `web` | Web API specifications (endpoints, authentication, CORS) |
| `data` | Data layer semantics (validation, transformation, querying) |
| `cli` | Command-line interface specifications |
| `orm` | Object-relational mapping patterns |
| `testing` | Test specifications (coverage, fixtures, mocking) |
| `events` | Event-driven patterns (emitters, handlers, subscriptions) |
| `state` | State management (Redux-like stores, XState machines) |
| `plugins` | Plugin system specifications |
| `serialization` | Serialization/deserialization patterns |

### Concern Extensions

Extensions that address cross-cutting concerns:

| Extension | Purpose |
|-----------|---------|
| `errors` | Error handling specifications (hierarchy, codes, recovery) |
| `perf` | Performance characteristics (complexity, benchmarks) |
| `safety` | Safety constraints (thread safety, memory safety) |
| `config` | Configuration specifications |
| `versioning` | API versioning and deprecation |
| `observability` | Logging, metrics, and tracing |
| `workflow` | Development workflow tracking (planned → tested → shipped) |

## Compatibility Matrix

All extensions are designed to be composable. This matrix highlights particularly synergistic combinations:

| Extension A | Extension B | Interaction |
|-------------|-------------|-------------|
| `workflow` | `testing` | `workflow_state: tested` should align with `test_coverage` specs |
| `workflow` | `versioning` | Deprecation evidence pairs with `deprecated_in` version |
| `async` | `state` | Orthogonal: async describes runtime behavior, state describes FSM APIs |
| `events` | `observability` | Event-emitting types benefit from metrics/tracing specs |
| `data` | `serialization` | Complementary: data validation + serialization formats |
| `errors` | `observability` | Error tracking integrates with observability metrics |

## Semantic Relationships

### workflow + testing

When both extensions are enabled, entities with tested workflow states should have corresponding test specifications:

```json
{
  "extensions": ["workflow", "testing"],
  "library": {
    "types": [{
      "name": "ConnectionPool",
      "workflow_state": "tested",
      "test_coverage": {
        "unit": { "percentage": 95 },
        "integration": { "percentage": 80 }
      }
    }]
  }
}
```

**Lint rule `E001`** warns when an entity has `workflow_state` in `{tested, documented, released}` but no `test_coverage` defined.

### workflow + versioning

Deprecation workflows benefit from combining workflow evidence with versioning metadata:

```json
{
  "extensions": ["workflow", "versioning"],
  "library": {
    "types": [{
      "name": "OldClient",
      "workflow_state": "deprecated",
      "state_evidence": [{
        "type": "deprecation_notice",
        "reference": "CHANGELOG.md",
        "date": "2024-06-01"
      }],
      "deprecated_in": "2.0.0",
      "removed_in": "3.0.0",
      "replacement": "#/types/NewClient"
    }]
  }
}
```

### async + state

These extensions describe different aspects and do not overlap:

- **async extension**: Models runtime object lifecycle (connection states, task states)
- **state extension**: Models state machine APIs the library exposes to users

A type can use both:

```json
{
  "extensions": ["async", "state"],
  "library": {
    "types": [{
      "name": "WorkflowEngine",
      "lifecycle": {
        "states": [
          { "name": "initializing" },
          { "name": "running" },
          { "name": "stopped", "terminal": true }
        ],
        "initial_state": "initializing"
      },
      "state_machines": [{
        "name": "document-workflow",
        "initial": "draft",
        "states": [
          { "name": "draft" },
          { "name": "review" },
          { "name": "published", "type": "final" }
        ]
      }]
    }]
  }
}
```

## Common Extension Combinations

### Web API Library

```json
{
  "extensions": ["async", "errors", "web", "observability"]
}
```

- `async`: Document async request handling
- `errors`: Define error responses and codes
- `web`: Specify endpoints, auth, CORS
- `observability`: Request tracing and metrics

### Data Processing Library

```json
{
  "extensions": ["data", "serialization", "errors", "perf"]
}
```

- `data`: Validation rules and transformations
- `serialization`: JSON/protobuf/msgpack support
- `errors`: Validation and parsing errors
- `perf`: Complexity and throughput specs

### CLI Application

```json
{
  "extensions": ["cli", "config", "errors"]
}
```

- `cli`: Commands, arguments, flags
- `config`: Configuration file formats
- `errors`: Exit codes and error messages

### State Management Library

```json
{
  "extensions": ["state", "events", "testing"]
}
```

- `state`: Store and state machine definitions
- `events`: Action dispatching patterns
- `testing`: Store testing utilities

## Cross-Extension Lint Rules

The following lint rules detect semantic conflicts between extensions:

| Rule | Extensions | Description |
|------|------------|-------------|
| `E001` | workflow + testing | Tested entity missing test_coverage specs |
| `E002` | workflow | Early-stage entity has implementation evidence |

Run extension-specific linting:

```bash
libspec lint --rule E001 spec.json
```

## Extension Precedence

When extensions define similar concepts, the more specific extension takes precedence for its domain:

1. **State models**: `state.py` defines `MachineStateSpec` for XState/FSM patterns; `async_.py` defines `AsyncStateSpec` for runtime object lifecycles; `workflow.py` defines `DevStateSpec` for development workflows. These are distinct concepts.

2. **Schema merging**: When `validate_spec()` merges extension schemas, core schema definitions take precedence over extension definitions with the same name.

## Adding New Extensions

When creating a new extension, consider:

1. **Field naming**: Prefix extension-specific fields to avoid collisions
2. **Semantic scope**: Document whether the extension describes runtime behavior, development process, or API contracts
3. **Complementary extensions**: Identify which existing extensions pair well with yours
4. **Lint rules**: Consider adding cross-extension rules if semantic relationships exist
