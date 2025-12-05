# Proposal 002: Method Decorator Support

## Status
Proposed

## Problem

Python methods often have decorators that fundamentally change their behavior:

- `@asynccontextmanager` - Method is an async context manager
- `@contextmanager` - Method is a sync context manager
- `@property` - Method is a property (already handled separately)
- `@classmethod` / `@staticmethod` - Method binding behavior
- `@overload` - Type stub overloads
- `@cache` / `@lru_cache` - Caching behavior
- Custom decorators - Library-specific behavior modifiers

Currently, libspec signatures strip decorator information:

```json
// Information lost - this is a context manager!
{
  "name": "nursery",
  "signature": "(self, *, error_policy: NurseryErrorPolicy = ...) -> AsyncIterator[Nursery]"
}
```

The return type `AsyncIterator[Nursery]` hints at context manager usage, but:
1. It's implicit, not explicit
2. Tooling can't reliably detect it
3. `@contextmanager` vs `@asynccontextmanager` distinction is lost

## Proposed Solution

Add a `decorators` field to `Method` and `FunctionDef`:

```python
class Method(LibspecModel):
    name: SnakeCaseOrDunderName
    signature: str
    async_: bool = Field(default=False, alias="async")
    description: str | None = None
    # ... existing fields ...

    # NEW FIELD
    decorators: list[str] = Field(
        default_factory=list,
        description="Decorators applied to this method (e.g., ['asynccontextmanager', 'cache'])"
    )
```

## Use Case

```json
{
  "name": "nursery",
  "signature": "(self, *, error_policy: NurseryErrorPolicy = NurseryErrorPolicy.FAIL_FAST) -> AsyncIterator[Nursery]",
  "async": true,
  "decorators": ["asynccontextmanager"],
  "description": "Create a nursery for spawning child actors with structured concurrency."
}
```

## Benefits

1. **Semantic clarity**: Explicit that method is a context manager
2. **Tooling support**: Generate correct usage patterns (`async with ctx.nursery()`)
3. **Documentation**: Users see decorator in generated docs
4. **Completeness**: Full method signature information preserved

## Alternative Considered

Encode decorators in the signature string itself:
```json
"signature": "@asynccontextmanager (self, ...) -> AsyncIterator[Nursery]"
```

Rejected because:
- Complicates signature parsing
- Mixes concerns (decoration vs parameters)
- Harder to query/filter programmatically

## Backwards Compatibility

New optional field with empty list default. Existing specs remain valid.
