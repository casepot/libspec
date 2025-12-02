"""TypedDict definitions for lifecycle extension types.

These provide type hints for the lifecycle extension schema structures,
enabling IDE autocomplete and static type checking without runtime overhead.
"""

from typing import Literal, TypedDict


# -----------------------------------------------------------------------------
# Evidence Types
# -----------------------------------------------------------------------------


class PrEvidence(TypedDict, total=False):
    """Pull/merge request evidence."""

    type: Literal["pr"]  # Required
    url: str  # Required
    description: str
    date: str  # ISO date format
    author: str


class TestsEvidence(TypedDict, total=False):
    """Test file/directory evidence."""

    type: Literal["tests"]  # Required
    path: str  # Required
    description: str
    date: str


class DesignDocEvidence(TypedDict, total=False):
    """Design document evidence."""

    type: Literal["design_doc"]  # Required
    reference: str  # Required - URL or path
    description: str
    date: str
    author: str


class DocsEvidence(TypedDict, total=False):
    """Documentation URL evidence."""

    type: Literal["docs"]  # Required
    url: str  # Required
    description: str
    date: str


class ApprovalEvidence(TypedDict, total=False):
    """Approval evidence - requires author."""

    type: Literal["approval"]  # Required
    reference: str  # Required
    author: str  # Required
    description: str
    date: str


class BenchmarkEvidence(TypedDict, total=False):
    """Benchmark results evidence."""

    type: Literal["benchmark"]  # Required
    reference: str  # Required
    metrics: dict[str, int | float | str]
    description: str
    date: str
    author: str


class MigrationGuideEvidence(TypedDict, total=False):
    """Migration guide evidence."""

    type: Literal["migration_guide"]  # Required
    reference: str  # Required
    description: str
    date: str


class DeprecationNoticeEvidence(TypedDict, total=False):
    """Deprecation notice evidence - requires date."""

    type: Literal["deprecation_notice"]  # Required
    reference: str  # Required
    date: str  # Required
    description: str


class CustomEvidence(TypedDict, total=False):
    """Custom evidence type defined in workflow."""

    type: Literal["custom"]  # Required
    type_name: str  # Required - references workflow evidence_types
    reference: str
    url: str
    path: str
    description: str
    date: str
    author: str


# Union of all evidence types
EvidenceSpec = (
    PrEvidence
    | TestsEvidence
    | DesignDocEvidence
    | DocsEvidence
    | ApprovalEvidence
    | BenchmarkEvidence
    | MigrationGuideEvidence
    | DeprecationNoticeEvidence
    | CustomEvidence
)


# -----------------------------------------------------------------------------
# Workflow Types
# -----------------------------------------------------------------------------


class GateSpec(TypedDict, total=False):
    """A gate condition for a transition."""

    type: str  # Required
    required: bool  # Default: True
    description: str
    validator: str  # For custom gates


class DevStateSpec(TypedDict, total=False):
    """A development lifecycle state."""

    name: str  # Required
    description: str
    terminal: bool  # Default: False
    required_evidence: list[str]
    order: int


class DevTransitionSpec(TypedDict, total=False):
    """A valid state transition with optional gates."""

    from_state: str  # Required
    to_state: str  # Required
    gates: list[GateSpec]
    description: str


class EvidenceTypeSpec(TypedDict, total=False):
    """Custom evidence type definition for a workflow."""

    name: str  # Required - snake_case
    description: str
    required_fields: list[Literal["reference", "url", "path", "author", "date"]]
    reference_pattern: str  # Regex for validating reference
    url_pattern: str  # Regex for validating url


class WorkflowSpec(TypedDict, total=False):
    """A named workflow defining development lifecycle states and transitions."""

    name: str  # Required
    description: str
    states: list[DevStateSpec]  # Required
    initial_state: str  # Required
    transitions: list[DevTransitionSpec]
    allow_skip: bool  # Default: False
    evidence_types: list[EvidenceTypeSpec]


# -----------------------------------------------------------------------------
# Entity Lifecycle Fields
# -----------------------------------------------------------------------------


class LifecycleFields(TypedDict, total=False):
    """Fields added to entities when lifecycle extension is active."""

    lifecycle_state: str
    workflow: str  # Workflow override
    state_evidence: list[EvidenceSpec]


# -----------------------------------------------------------------------------
# Library Extension Fields
# -----------------------------------------------------------------------------


class LifecycleLibraryFields(TypedDict, total=False):
    """Fields added to Library when lifecycle extension is active."""

    workflows: list[WorkflowSpec]
    default_workflow: str


# -----------------------------------------------------------------------------
# Collected Entity (for lifecycle command)
# -----------------------------------------------------------------------------


class LifecycleEntity(TypedDict):
    """An entity with lifecycle tracking (collected for reporting)."""

    entity_type: Literal["type", "function", "feature", "method"]
    name: str
    ref: str  # JSON pointer reference
    lifecycle_state: str
    workflow: str | None
    state_evidence: list[EvidenceSpec]


class BlockedItem(TypedDict):
    """An entity blocked from transitioning due to unsatisfied gates."""

    entity: str  # JSON pointer reference
    name: str
    current_state: str
    blocked_transition: str
    unsatisfied_gates: list[str]


class GateStatus(TypedDict):
    """Status of a gate check."""

    gate: str
    required: bool
    satisfied: bool
