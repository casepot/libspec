# libspec

A schema system for documenting library interfaces, architecture, and behavioral specifications.

## Overview

libspec provides a structured, machine-readable format for describing Python libraries. It enables:

- **Systematic querying** of interfaces (types, functions, methods)
- **Machine validation** of specification files
- **Behavioral specifications** linked to testable assertions
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

## Schema Structure

### Core Schema

The core schema captures universal library concepts:

- **Library**: Root container with name, version, description
- **Principles**: Design philosophy and anti-patterns
- **Modules**: Package structure and dependencies
- **Types**: Classes, protocols, enums, dataclasses, type aliases
- **Functions**: Functions, decorators, context managers
- **Features**: Behavioral specifications with test steps

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

## Cross-References

Reference other entities within or across specs:

```
Internal:   #/types/Handle
            #/types/Handle/methods/send
            #/functions/spawn
            #/features/ACTOR_001

External:   other_lib#/types/SomeType
```

## Documentation

- [Core Schema Reference](docs/core.md)
- [Extension Reference](docs/extensions/)
- [Usage Guide](docs/usage.md)
- [Examples](docs/examples/)

## License

MIT
