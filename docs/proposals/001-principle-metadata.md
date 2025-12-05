# Proposal 001: Principle Metadata Extension

## Status
Proposed

## Problem

The current `Principle` schema is too restrictive for real-world use. When specifying design principles for a library, users need to:

1. **Categorize principles** - Group related principles (e.g., "actor_model", "error_handling", "concurrency")
2. **Cross-reference entities** - Link principles to the types/functions they govern
3. **Track provenance** - Record where principles originated (design docs, discussions, ADRs)

The current schema only allows:
```python
class Principle(LibspecModel):
    id: KebabCaseId
    statement: NonEmptyStr
    rationale: str | None
    implications: list[str]
    anti_patterns: list[str]
```

## Proposed Solution

Extend the Principle schema with three optional fields:

```python
class Principle(LibspecModel):
    id: KebabCaseId
    statement: NonEmptyStr
    rationale: str | None
    implications: list[str]
    anti_patterns: list[str]

    # NEW FIELDS
    category: str | None = Field(
        default=None,
        description="Category for grouping related principles (e.g., 'actor_model', 'error_handling')"
    )
    refs: list[CrossReference] = Field(
        default_factory=list,
        description="Cross-references to types/functions this principle governs"
    )
    source: str | None = Field(
        default=None,
        description="Provenance: where this principle originated (e.g., 'design.md:45-47', 'ADR-003')"
    )
```

## Use Case

From a real library spec (weave):

```json
{
  "id": "generator-dual-channel",
  "category": "actor_model",
  "statement": "Generator actors separate observability (Stream) from orchestration (Result)",
  "rationale": "Enables 'Chain of Thought' decoupling...",
  "implications": ["Generator actors define both YieldType and ReturnType", ...],
  "anti_patterns": ["Returning final results via yield", ...],
  "refs": ["#/types/GeneratorActorDef", "#/types/GeneratorHandle"],
  "source": "DESIGN_INVARIANTS feature"
}
```

## Benefits

1. **Organization**: Filter/group principles by category in tooling
2. **Traceability**: Navigate from principle → governed entities
3. **Auditability**: Track where design decisions came from

## Backwards Compatibility

All new fields are optional with sensible defaults. Existing specs remain valid.
