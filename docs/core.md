# Core Schema Reference

This document describes the core libspec schema, which captures universal concepts applicable to any Python library.

## Schema Structure

```
libspec.json
├── $schema: "libspec/1.0"
├── extensions: ["async", "errors", ...]
└── library
    ├── name, version, tagline, description
    ├── principles: [Principle, ...]
    ├── modules: [Module, ...]
    ├── types: [TypeDef, ...]
    ├── functions: [FunctionDef, ...]
    └── features: [Feature, ...]
```

## Root Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string | Yes | Schema version, e.g., `"libspec/1.0"` |
| `extensions` | string[] | No | List of extension names to apply |
| `library` | Library | Yes | The library specification |

## Library

The root container for a library specification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Package name (lowercase, underscores) |
| `version` | string | Yes | Semantic version (e.g., `"1.0.0"`) |
| `python_requires` | string | No | Python version requirement (e.g., `">=3.10"`) |
| `tagline` | string | No | One-line description (max 100 chars) |
| `description` | string | No | Longer description (Markdown) |
| `repository` | string | No | URL to source repository |
| `documentation` | string | No | URL to documentation |
| `principles` | Principle[] | No | Design principles |
| `modules` | Module[] | No | Package structure |
| `types` | TypeDef[] | No | Type definitions |
| `functions` | FunctionDef[] | No | Top-level functions |
| `features` | Feature[] | No | Behavioral specifications |

### Example

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

---

## Principle

Design principles that guide library decisions.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (kebab-case) |
| `statement` | string | Yes | Brief principle statement |
| `rationale` | string | No | Why this principle exists |
| `implications` | string[] | No | Concrete implications |
| `anti_patterns` | string[] | No | What this principle forbids |

### Example

```json
{
  "id": "agents-are-coroutines",
  "statement": "Agents are just coroutines",
  "rationale": "Simplifies mental model and enables standard async patterns",
  "implications": [
    "No class inheritance hierarchy for agents",
    "Each agent has a mailbox",
    "Context injection via first parameter"
  ],
  "anti_patterns": [
    "Subclassing a base Agent class",
    "Implicit global state"
  ]
}
```

---

## Module

Package structure and dependencies.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `path` | string | Yes | Dotted module path |
| `description` | string | No | What this module provides |
| `exports` | string[] | No | Public names exported |
| `depends_on` | string[] | No | Internal module dependencies |
| `external_deps` | string[] | No | External package dependencies |
| `internal` | boolean | No | Whether this is private (default: false) |

### Example

```json
{
  "path": "mylib.runtime",
  "description": "Core runtime primitives",
  "exports": ["Context", "Handle", "spawn"],
  "depends_on": ["mylib.events"],
  "external_deps": ["asyncio"]
}
```

---

## TypeDef

Type definitions: classes, protocols, enums, dataclasses, type aliases.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Type name |
| `kind` | enum | Yes | One of: `class`, `dataclass`, `protocol`, `enum`, `type_alias`, `namedtuple` |
| `module` | string | Yes | Module where defined |
| `generic_params` | GenericParam[] | No | Generic type parameters |
| `bases` | string[] | No | Base classes or protocols |
| `docstring` | string | No | What this type represents |
| `type_target` | string | No | For type_alias: the aliased type |
| `properties` | Property[] | No | Instance properties |
| `methods` | Method[] | No | Instance methods |
| `class_methods` | Method[] | No | Class methods |
| `static_methods` | Method[] | No | Static methods |
| `values` | EnumValue[] | No | Enum values (for kind='enum') |
| `invariants` | string[] | No | Statements always true for valid instances |
| `construction` | Constructor | No | Constructor specification |
| `related` | string[] | No | Cross-references to related entities |
| `example` | string | No | Usage example |

### Example: Class

```json
{
  "name": "Handle",
  "kind": "class",
  "module": "mylib.runtime",
  "generic_params": [{"name": "T"}],
  "docstring": "User-facing reference to a running actor instance",
  "properties": [
    {"name": "id", "type": "ActorId", "readonly": true},
    {"name": "status", "type": "ActorStatus", "readonly": true}
  ],
  "methods": [
    {
      "name": "send",
      "signature": "(message: Any) -> None",
      "description": "Send a message to this actor's mailbox",
      "raises": [
        {"type": "InvalidActorState", "when": "actor is in terminal state"}
      ]
    }
  ],
  "invariants": [
    "Awaiting returns T on COMPLETED, raises on FAILED/CANCELLED"
  ]
}
```

### Example: Enum

```json
{
  "name": "ActorStatus",
  "kind": "enum",
  "module": "mylib.runtime",
  "values": [
    {"name": "RUNNING", "description": "Actor is actively executing"},
    {"name": "WAITING", "description": "Blocked in await"},
    {"name": "COMPLETED", "description": "Finished successfully"},
    {"name": "FAILED", "description": "Raised exception"},
    {"name": "CANCELLED", "description": "Cancelled externally"}
  ]
}
```

### Example: Protocol

```json
{
  "name": "LLMEngine",
  "kind": "protocol",
  "module": "mylib.llm",
  "docstring": "Abstract engine that satisfies ctx.act()",
  "properties": [
    {"name": "supports_streaming", "type": "bool", "readonly": true}
  ],
  "methods": [
    {
      "name": "run",
      "signature": "(request: LLMRequest) -> LLMResult[Any]"
    }
  ]
}
```

---

## GenericParam

Generic type parameter specification.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name (e.g., `"T"`) |
| `bound` | string | No | Upper bound constraint |
| `variance` | enum | No | `invariant`, `covariant`, or `contravariant` (default: invariant) |
| `default` | string | No | Default type (Python 3.12+) |

### Example

```json
{"name": "T", "bound": "BaseModel", "variance": "covariant"}
```

---

## Property

Instance property or attribute.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Property name |
| `type` | string | Yes | Type annotation |
| `readonly` | boolean | No | Whether read-only (default: false) |
| `default` | string | No | Default value (as string) |
| `description` | string | No | What this property represents |

---

## Method

Method definition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Method name |
| `signature` | string | Yes | Full signature |
| `description` | string | No | What this method does |
| `parameters` | Parameter[] | No | Detailed parameter specs |
| `returns` | ReturnSpec | No | Return value spec |
| `preconditions` | string[] | No | State requirements before call |
| `postconditions` | string[] | No | Guaranteed state after call |
| `raises` | RaisesClause[] | No | Exceptions that may be raised |
| `inherited_from` | string | No | Base class (if inherited) |

---

## Parameter

Function or method parameter.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Parameter name |
| `type` | string | Yes | Type annotation |
| `default` | string | No | Default value (`"REQUIRED"` means required) |
| `description` | string | No | What this parameter controls |
| `kind` | enum | No | Parameter kind: `positional_only`, `positional_or_keyword`, `keyword_only`, `var_positional`, `var_keyword` |

---

## RaisesClause

Exception that may be raised.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | Exception type name |
| `when` | string | Yes | Condition when raised |

---

## FunctionDef

Top-level function definition.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Function name |
| `kind` | enum | Yes | `function`, `decorator`, `context_manager`, `async_context_manager` |
| `module` | string | Yes | Module where defined |
| `signature` | string | Yes | Full signature |
| `generic_params` | GenericParam[] | No | Generic type parameters |
| `parameters` | Parameter[] | No | Detailed parameter specs |
| `returns` | ReturnSpec | No | Return value spec |
| `yields` | YieldSpec | No | Yield value spec (generators) |
| `description` | string | No | What this function does |
| `preconditions` | string[] | No | State requirements before call |
| `postconditions` | string[] | No | Guaranteed state after call |
| `invariants` | string[] | No | Invariants maintained |
| `raises` | RaisesClause[] | No | Exceptions that may be raised |
| `idempotent` | boolean | No | Multiple calls same as one? |
| `pure` | boolean | No | No side effects? |
| `deterministic` | boolean | No | Same inputs → same outputs? |
| `related` | string[] | No | Cross-references |
| `example` | string | No | Usage example |

### Example

```json
{
  "name": "spawn",
  "kind": "function",
  "module": "mylib.runtime",
  "signature": "(actor: ActorDef[P, T], *args, parent: Handle[Any] | None = None) -> Handle[T]",
  "description": "Create a new actor instance",
  "postconditions": [
    "spawn() is non-blocking; returns Handle immediately",
    "Each spawn gets fresh actor ID and mailbox"
  ],
  "invariants": [
    "Parent/child tree is strictly hierarchical (no cycles)"
  ]
}
```

---

## Feature

Behavioral specification with test steps.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier |
| `category` | string | Yes | Category (SCREAMING_SNAKE_CASE) |
| `summary` | string | No | One-line summary (max 100 chars) |
| `description` | string | Yes | Detailed behavioral description |
| `steps` | string[] | No | Verification/test steps |
| `references` | string[] | No | Cross-references to types/methods |
| `status` | enum | No | `planned`, `implemented`, `tested` (default: planned) |
| `breaking_since` | string? | No | Version where breaking (null if never) |
| `v1_planned` | string[] | No | Features planned for v1 |

### Example

```json
{
  "id": "actor-id-uniqueness",
  "category": "ACTOR_IDENTITY_METADATA",
  "summary": "Every spawned actor has unique ActorId",
  "description": "The runtime guarantees no two actors share the same identifier...",
  "steps": [
    "Spawn 100 actors concurrently",
    "Collect all handle.id values into a set",
    "Assert the set size equals 100"
  ],
  "references": ["#/types/ActorId", "#/functions/spawn"],
  "status": "planned"
}
```

---

## Cross-References

Reference syntax for linking entities:

| Pattern | Meaning |
|---------|---------|
| `#/types/TypeName` | Type in same spec |
| `#/types/TypeName/methods/methodName` | Method on a type |
| `#/functions/funcName` | Function in same spec |
| `#/features/FEATURE_ID` | Feature in same spec |
| `otherlib#/types/TypeName` | Type in another spec |
