# Proposal 005: Generic Parameter Descriptions

## Status
Proposed

## Problem

Generic type parameters often have semantic meaning that's not captured by their name alone:

```python
class ActorDef(Generic[P, T]):
    """
    P: ParamSpec capturing the actor function's parameters
    T: The return type of the actor
    """
    pass
```

Current libspec schema for `GenericParam`:

```python
class GenericParam(LibspecModel):
    name: str
    variance: GenericVariance
    bound: TypeAnnotationStr | None
    # No description field!
```

This means we lose documentation:

```json
// Information lost
{
  "name": "P",
  "variance": "invariant",
  "bound": "ParamSpec"
  // Where did "Function parameter specification" go?
}
```

## Proposed Solution

Add optional `description` field to `GenericParam`:

```python
class GenericParam(LibspecModel):
    name: str
    variance: GenericVariance
    bound: TypeAnnotationStr | None
    description: str | None = Field(
        default=None,
        description="What this type parameter represents semantically"
    )
```

## Use Case

```json
{
  "name": "ActorDef",
  "kind": "class",
  "generic_params": [
    {
      "name": "P",
      "variance": "invariant",
      "bound": "ParamSpec",
      "description": "Parameter specification capturing the actor function's signature"
    },
    {
      "name": "T",
      "variance": "covariant",
      "bound": null,
      "description": "Return type of the actor - what await handle returns"
    }
  ]
}
```

## Benefits

1. **Self-documenting**: Users understand what `T` means in context
2. **Consistency**: Other schema elements (parameters, properties) have descriptions
3. **Tooling**: Generate better documentation for generic types

## Backwards Compatibility

New optional field. Existing specs remain valid.
