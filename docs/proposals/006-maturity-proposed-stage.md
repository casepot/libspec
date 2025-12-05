# Proposal 006: Add "proposed" Maturity Stage

## Status
Proposed

## Problem

Current `EntityMaturity` enum:

```python
class EntityMaturity(str, Enum):
    IDEA = "idea"           # Rough concept
    SPECIFIED = "specified" # Behavior described
    DESIGNED = "designed"   # Shape defined
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DOCUMENTED = "documented"
    RELEASED = "released"
    DEPRECATED = "deprecated"
```

There's a gap between `idea` and `specified`:

- **idea**: Rough concept, may change significantly
- **???**: Proposed for inclusion, under discussion, not yet specified
- **specified**: Behavior described, acceptance criteria clear

Real projects have features that are:
- Proposed in an RFC/discussion
- Agreed to pursue but not yet specified
- In design review

## Proposed Solution

Add `proposed` stage between `idea` and `specified`:

```python
class EntityMaturity(str, Enum):
    IDEA = "idea"           # Rough concept, exploratory
    PROPOSED = "proposed"   # NEW: Formally proposed, under consideration
    SPECIFIED = "specified" # Behavior described, acceptance criteria clear
    DESIGNED = "designed"   # Shape defined (signatures, types)
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DOCUMENTED = "documented"
    RELEASED = "released"
    DEPRECATED = "deprecated"
```

## Stage Definitions

| Stage | Description | Artifacts |
|-------|-------------|-----------|
| idea | Exploratory concept | Notes, sketches |
| **proposed** | Formally proposed for inclusion | RFC, proposal doc, discussion thread |
| specified | Behavior fully described | Acceptance criteria, user stories |
| designed | Technical shape defined | Type signatures, API surface |

## Use Case

```json
{
  "id": "distributed-tracing",
  "category": "OBSERVABILITY",
  "summary": "Distributed tracing integration with OpenTelemetry",
  "maturity": "proposed",  // RFC open, not yet specified
  "description": "..."
}
```

## Benefits

1. **Accuracy**: Features aren't forced into wrong buckets
2. **Workflow**: Matches real development process (propose → specify → design → build)
3. **Visibility**: Stakeholders see what's under consideration vs committed

## Backwards Compatibility

Additive change. Existing maturity values remain valid.
