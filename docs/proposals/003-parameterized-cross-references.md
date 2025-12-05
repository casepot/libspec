# Proposal 003: Parameterized Cross-References

## Status
Proposed

## Problem

Current cross-references cannot express generic type relationships:

```json
// Current: loses type parameter binding
"bases": ["#/types/Handle"]

// What we need to express:
"bases": ["Handle[ReturnT]"]  // GeneratorHandle extends Handle with ReturnT bound
```

This matters for:
1. **Inheritance**: `class GeneratorHandle(Handle[ReturnT])` - which type param is bound?
2. **Composition**: `results: dict[str, Handle[T]]` - parameterized container types
3. **Constraints**: `T: Comparable[T]` - self-referential bounds

## Proposed Solution

### Option A: Extended Cross-Reference Syntax

Allow type parameters in cross-references:

```
CrossReference =
  | "#/types/TypeName"                    # Simple reference
  | "#/types/TypeName[Param, ...]"        # Parameterized reference
```

Example:
```json
{
  "name": "GeneratorHandle",
  "generic_params": [
    {"name": "YieldT", "variance": "covariant"},
    {"name": "ReturnT", "variance": "covariant"}
  ],
  "bases": ["#/types/Handle[ReturnT]"]
}
```

### Option B: Structured Base Type

Use an object instead of string for bases:

```json
{
  "bases": [
    {
      "ref": "#/types/Handle",
      "type_args": ["ReturnT"]
    }
  ]
}
```

## Recommendation

**Option A** - Extended syntax is more readable and consistent with Python's `Handle[ReturnT]` notation. The cross-reference pattern becomes:

```regex
^([a-z_][a-z0-9_.]*)?#/(types|functions|features|principles|modules)/[a-zA-Z_][a-zA-Z0-9_-]*(\[.+\])?$
```

## Use Cases

```json
// Inheritance with bound type parameter
{
  "name": "GeneratorHandle",
  "bases": ["#/types/Handle[ReturnT]"]
}

// Multiple inheritance with different bindings
{
  "name": "AsyncChannel",
  "bases": ["#/types/Channel[T]", "#/types/AsyncIterable[T]"]
}
```

## Benefits

1. **Type precision**: Exact generic relationships preserved
2. **Documentation**: Generated docs show correct inheritance
3. **Analysis**: Tooling can track type parameter flow

## Backwards Compatibility

Existing simple cross-references remain valid. New parameterized syntax is additive.
