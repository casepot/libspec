# Proposal 004: External Type References

## Status
Proposed

## Problem

Libraries don't exist in isolation. They inherit from, compose with, and depend on external types:

```python
from pydantic import BaseModel

class ActorOptions(BaseModel):  # Inherits from external type
    name: str
    restart_policy: RestartPolicy
```

Current libspec cannot represent this:

```json
// This gets rejected - not a valid cross-reference
"bases": ["pydantic.BaseModel"]

// This loses information - where does BaseModel come from?
"bases": []  // Removed!
```

## Proposed Solution

Support qualified external type references:

```
ExternalReference = "module.path:TypeName"
CrossReference = InternalRef | ExternalRef

InternalRef = "#/types/TypeName"
ExternalRef = "package.module:TypeName"
```

Examples:
```json
"bases": ["pydantic:BaseModel"]
"bases": ["typing:Protocol"]
"bases": ["collections.abc:Mapping"]
"related": ["#/types/Handle", "asyncio:Task"]
```

## Schema Changes

```python
# New pattern for cross-references
CrossReference = Annotated[
    str,
    Field(pattern=r'^(#/(types|functions|features|principles|modules)/[a-zA-Z_][a-zA-Z0-9_-]*|[a-z_][a-z0-9_.]*:[A-Z][a-zA-Z0-9_]*)$')
]
```

## Use Cases

### 1. Framework Integration
```json
{
  "name": "ActorOptions",
  "bases": ["pydantic:BaseModel"],
  "docstring": "Configuration options for actor spawning, validated via Pydantic."
}
```

### 2. Protocol Implementation
```json
{
  "name": "Channel",
  "bases": ["typing:Generic[T]", "collections.abc:AsyncIterator"],
  "docstring": "Async channel for inter-actor communication."
}
```

### 3. Related External Types
```json
{
  "name": "Handle",
  "related": ["#/types/Context", "asyncio:Task", "asyncio:Future"]
}
```

## Benefits

1. **Completeness**: Full inheritance chain documented
2. **Dependency visibility**: See what external packages are used
3. **User understanding**: "Oh, this is a Pydantic model, I know how those work"

## Open Questions

1. Should we validate that external references are real packages?
2. Should we track version requirements for external deps?
3. How to handle stdlib vs third-party distinction?

## Backwards Compatibility

New reference format is additive. Existing internal references unchanged.
