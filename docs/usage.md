# Usage Guide

This guide explains how to use libspec to document your Python library.

## Getting Started

### Installation

```bash
# Core library only
pip install libspec

# With CLI tools (recommended)
pip install libspec[cli]
```

The CLI provides commands for exploring, validating, and linting your specs. See [CLI Reference](cli.md) for full documentation.

### Creating Your First Spec

Create a `specs/libspec.json` file in your project:

```json
{
  "$schema": "libspec/1.0",
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "tagline": "A library for doing things",
    "python_requires": ">=3.10"
  }
}
```

This is the minimal valid specification. From here, you can add types, functions, and features.

### Directory Structure

We recommend placing specs alongside your source code:

```
mylib/
├── src/
│   └── mylib/
│       └── ...
├── specs/
│   ├── libspec.json      # Main specification
│   └── features/         # Optional: split feature files
│       ├── core.json
│       └── concurrency.json
└── tests/
```

## Adding Types

Document your classes, protocols, and enums:

```json
{
  "$schema": "libspec/1.0",
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "types": [
      {
        "name": "Connection",
        "kind": "class",
        "module": "mylib.client",
        "docstring": "A connection to the remote service",
        "properties": [
          {
            "name": "is_connected",
            "type": "bool",
            "readonly": true,
            "description": "Whether the connection is active"
          }
        ],
        "methods": [
          {
            "name": "send",
            "signature": "(self, message: bytes) -> None",
            "description": "Send a message over the connection",
            "preconditions": ["is_connected is True"],
            "raises": [
              {"type": "ConnectionError", "when": "connection is closed"}
            ]
          }
        ],
        "invariants": [
          "After close(), is_connected is always False"
        ]
      }
    ]
  }
}
```

### Type Kinds

| Kind | Description |
|------|-------------|
| `class` | Regular Python class |
| `dataclass` | @dataclass decorated class |
| `protocol` | typing.Protocol (structural subtyping) |
| `enum` | Enum class with named values |
| `type_alias` | Type alias (TypeAlias) |
| `namedtuple` | NamedTuple class |

## Adding Functions

Document module-level functions:

```json
{
  "functions": [
    {
      "name": "connect",
      "kind": "function",
      "module": "mylib.client",
      "signature": "(host: str, port: int = 8080, *, timeout: float = 30.0) -> Connection",
      "description": "Create a new connection to the service",
      "parameters": [
        {
          "name": "host",
          "type": "str",
          "description": "Hostname to connect to"
        },
        {
          "name": "port",
          "type": "int",
          "default": "8080",
          "description": "Port number"
        },
        {
          "name": "timeout",
          "type": "float",
          "default": "30.0",
          "kind": "keyword_only",
          "description": "Connection timeout in seconds"
        }
      ],
      "returns": {
        "type": "Connection",
        "description": "Active connection to the service"
      },
      "raises": [
        {"type": "ConnectionError", "when": "unable to connect"},
        {"type": "TimeoutError", "when": "connection times out"}
      ]
    }
  ]
}
```

### Function Kinds

| Kind | Description |
|------|-------------|
| `function` | Regular function |
| `decorator` | Function that decorates other functions |
| `context_manager` | Context manager (sync) |
| `async_context_manager` | Async context manager |

## Using Extensions

Extensions add domain-specific fields to your specification.

### Enabling Extensions

List extensions in the root of your spec:

```json
{
  "$schema": "libspec/1.0",
  "extensions": ["async", "errors", "observability"],
  "library": { ... }
}
```

### Async Extension

When `async` is enabled, you can document async behavior:

```json
{
  "types": [
    {
      "name": "Actor",
      "kind": "class",
      "module": "mylib.runtime",
      "lifecycle": {
        "states": [
          {"name": "INIT", "description": "Created but not started"},
          {"name": "RUNNING", "description": "Actively processing"},
          {"name": "COMPLETED", "description": "Finished successfully", "terminal": true},
          {"name": "FAILED", "description": "Finished with error", "terminal": true}
        ],
        "initial_state": "INIT",
        "transitions": [
          {"from": "INIT", "to": "RUNNING", "trigger": "start()"},
          {"from": "RUNNING", "to": "COMPLETED", "trigger": "normal completion"},
          {"from": "RUNNING", "to": "FAILED", "trigger": "exception raised"}
        ]
      },
      "methods": [
        {
          "name": "run",
          "signature": "(self) -> T",
          "async": true,
          "cancellation": {
            "mode": "cooperative",
            "cleanup": "Resources released, children cancelled"
          }
        }
      ]
    }
  ]
}
```

### Errors Extension

Document your exception hierarchy:

```json
{
  "library": {
    "error_hierarchy": [
      {
        "type": "MyLibError",
        "base": "Exception",
        "description": "Base for all library errors",
        "children": ["ConnectionError", "ValidationError"]
      }
    ],
    "exceptions": [
      {
        "type": "ConnectionError",
        "module": "mylib.errors",
        "base": "MyLibError",
        "description": "Failed to connect to service",
        "fields": [
          {"name": "host", "type": "str"},
          {"name": "port", "type": "int"}
        ],
        "recovery": "Check network connectivity and retry",
        "retryable": true
      }
    ],
    "error_codes": [
      {
        "code": "E001",
        "type": "ConnectionError",
        "description": "Connection refused",
        "docs_url": "https://docs.mylib.dev/errors/E001"
      }
    ]
  }
}
```

### Observability Extension

Document logging, metrics, and tracing:

```json
{
  "library": {
    "logging": {
      "logger_name": "mylib",
      "levels_used": ["DEBUG", "INFO", "WARNING", "ERROR"],
      "structured": true,
      "context_fields": ["request_id", "user_id"]
    },
    "metrics": [
      {
        "name": "mylib_requests_total",
        "type": "counter",
        "labels": ["method", "status"],
        "description": "Total requests processed"
      },
      {
        "name": "mylib_request_duration_seconds",
        "type": "histogram",
        "labels": ["method"],
        "buckets": [0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
        "description": "Request duration"
      }
    ],
    "tracing": {
      "span_names": ["mylib.connect", "mylib.send", "mylib.receive"],
      "propagation": "w3c"
    }
  }
}
```

## Behavioral Specifications (Features)

Features link documentation to testable assertions:

```json
{
  "features": [
    {
      "id": "connection-retry",
      "category": "CONNECTION",
      "summary": "Failed connections are automatically retried",
      "description": "When a connection attempt fails with a retryable error, the client automatically retries up to 3 times with exponential backoff.",
      "steps": [
        "Create a client with retry enabled",
        "Attempt to connect to an unavailable host",
        "Verify that 3 connection attempts are made",
        "Verify exponential backoff between attempts (1s, 2s, 4s)"
      ],
      "references": ["#/types/Client/methods/connect", "#/functions/connect"],
      "status": "tested"
    }
  ]
}
```

### Feature Status

| Status | Meaning |
|--------|---------|
| `planned` | Not yet implemented |
| `implemented` | Code exists but not fully tested |
| `tested` | Covered by automated tests |

## Cross-References

Reference other entities within your spec:

```
#/types/Connection                    → Type named "Connection"
#/types/Connection/methods/send       → Method "send" on Connection
#/functions/connect                   → Function named "connect"
#/features/connection-retry           → Feature by ID
```

Reference entities in other specs:

```
other_lib#/types/HttpClient           → Type in another library's spec
```

Use cross-references in:
- `related` fields on types and functions
- `references` fields on features
- `replacement` fields in deprecations

## Validation

### Using the CLI

The recommended way to validate specs:

```bash
# Schema validation
libspec validate

# Semantic linting (naming, completeness, consistency)
libspec lint

# Strict mode for CI (exits non-zero on issues)
libspec validate --strict && libspec lint --strict
```

Strict mode tightens validation beyond the core schema:
- Extension fields use strict booleans/ints/floats for risky flags (async/awaitable/blocking, retry/jitter, deterministic/idempotent/pure) instead of coercing truthy values.
- Numeric fields gain bounds (timeouts, rate limits, status codes, retry limits, coverage thresholds, middleware order, concurrency/capacity).
- Performance benchmarks use decimal types with `gt 0` to avoid float drift.
- Path-like fields must exist when strict: lifecycle evidence, coverage targets, config file locations, plugin discovery directories, and ORM migration directories.

### Using the Python API

```python
from libspec import validate_spec

errors = validate_spec("specs/libspec.json")
if errors:
    for error in errors:
        print(f"Validation error: {error}")
else:
    print("Spec is valid!")
```

## Exploring Your Spec

The CLI provides commands for progressive exploration:

```bash
# Overview with counts and coverage
libspec info

# List entities
libspec types
libspec functions
libspec features --status planned

# Search across the spec
libspec search "connection"

# Drill into specific entities
libspec refs '#/types/Connection'

# Custom jq queries
libspec query '.library.types[] | select(.kind=="protocol")'
```

Use `--text` for compact, token-efficient output:

```bash
$ libspec types --text
TYPE class Connection mylib.client
TYPE protocol Handler mylib.handlers
---
2 types
```

See [CLI Reference](cli.md) for the complete command reference.

## Best Practices

1. **Start minimal**: Begin with just library metadata and add detail incrementally

2. **Document contracts**: Focus on preconditions, postconditions, and invariants—these are more valuable than prose descriptions

3. **Link to tests**: Use features to connect your spec to actual test cases

4. **Use extensions**: Enable only the extensions you need to keep specs focused

5. **Keep in sync**: Update specs when you change APIs, ideally as part of the same commit

6. **Split large specs**: For large libraries, split features into separate files in `specs/features/`

## Further Reading

- [CLI Reference](cli.md) - Complete command reference with examples
- [Core Schema Reference](core.md) - All schema fields documented

### Extension Documentation

- [Async Extension](extensions/async.md)
- [Errors Extension](extensions/errors.md)
- [Performance Extension](extensions/perf.md)
- [Safety Extension](extensions/safety.md)
- [Configuration Extension](extensions/config.md)
- [Versioning Extension](extensions/versioning.md)
- [Observability Extension](extensions/observability.md)
