"""Workflow extension models for development workflow tracking.

This extension provides:
- Workflow definitions with states and transitions
- Evidence types for tracking progress (PRs, tests, docs, etc.)
- Workflow state fields for entities (types, functions, features)
"""

from __future__ import annotations

import re
from datetime import date as date_type
from pathlib import Path
from typing import Annotated, Literal, Union

from pydantic import (
    Field,
    HttpUrl,
    NonNegativeInt,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from ..base import ExtensionModel
from ..types import EntityMaturity, KebabCaseId, LocalPath, NonEmptyStr, PathOrUrl
from ..utils import ensure_strict_bool, validate_local_path, validate_path_or_url

# -----------------------------------------------------------------------------
# Evidence Types (Discriminated Union Members)
# -----------------------------------------------------------------------------


class EvidenceBase(ExtensionModel):
    """Base fields shared by all evidence types."""

    description: str | None = None
    date: date_type | None = None  # ISO date format


class PrEvidence(EvidenceBase):
    """Pull/merge request evidence."""

    type: Literal["pr"]
    url: HttpUrl  # Required URL to the PR
    author: str | None = None


class TestsEvidence(EvidenceBase):
    """Test file/directory evidence."""

    type: Literal["tests"]
    path: LocalPath

    @field_validator("path")
    @classmethod
    def validate_test_path(cls, v: str | Path, info: ValidationInfo) -> str | Path:
        """L009: Validate test path looks like a test file."""
        # Common test file patterns
        path_str = str(v)
        patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r"tests?/",
            r"spec/",
            r".*\.spec\.(ts|js)$",
            r".*\.test\.(ts|js)$",
        ]
        if not any(re.search(p, path_str) for p in patterns):
            raise ValueError(f"Path does not look like a test file: {v}")
        return validate_local_path(v, info, "path")


class DesignDocEvidence(EvidenceBase):
    """Design document evidence."""

    type: Literal["design_doc"]
    reference: PathOrUrl  # URL or path to design doc
    author: str | None = None

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str | Path, info: ValidationInfo) -> str | Path:
        return validate_path_or_url(v, info, "reference")


class DocsEvidence(EvidenceBase):
    """Documentation URL evidence."""

    type: Literal["docs"]
    url: HttpUrl | None


class ApprovalEvidence(EvidenceBase):
    """Approval evidence - requires author."""

    type: Literal["approval"]
    reference: PathOrUrl
    author: NonEmptyStr  # Required for approvals


class BenchmarkEvidence(EvidenceBase):
    """Benchmark results evidence."""

    type: Literal["benchmark"]
    reference: PathOrUrl
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    author: str | None = None

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str | Path, info: ValidationInfo) -> str | Path:
        return validate_path_or_url(v, info, "reference")


class MigrationGuideEvidence(EvidenceBase):
    """Migration guide evidence."""

    type: Literal["migration_guide"]
    reference: PathOrUrl

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str | Path, info: ValidationInfo) -> str | Path:
        return validate_path_or_url(v, info, "reference")


class DeprecationNoticeEvidence(EvidenceBase):
    """Deprecation notice evidence - requires date."""

    type: Literal["deprecation_notice"]
    reference: NonEmptyStr
    # Required for deprecation notices (intentionally narrows base class optional to required)
    date: date_type = Field(..., description="Date of the deprecation notice")  # pyright: ignore[reportIncompatibleVariableOverride,reportGeneralTypeIssues]


class CustomEvidence(EvidenceBase):
    """Custom evidence type defined in workflow."""

    type: Literal["custom"]
    type_name: NonEmptyStr  # References workflow evidence_types
    reference: str | None = None
    url: HttpUrl | None = None
    path: LocalPath | None = None
    author: str | None = None

    @field_validator("path")
    @classmethod
    def validate_optional_path(cls, v: str | Path | None, info: ValidationInfo) -> str | Path | None:
        if v is None:
            return None
        return validate_local_path(v, info, "path")

    @field_validator("reference")
    @classmethod
    def validate_optional_reference(cls, v: str | Path | None, info: ValidationInfo) -> str | Path | None:
        if v is None:
            return None
        return validate_path_or_url(v, info, "reference")


# Discriminated union of all evidence types
EvidenceSpec = Annotated[
    Union[
        PrEvidence,
        TestsEvidence,
        DesignDocEvidence,
        DocsEvidence,
        ApprovalEvidence,
        BenchmarkEvidence,
        MigrationGuideEvidence,
        DeprecationNoticeEvidence,
        CustomEvidence,
    ],
    Field(discriminator="type"),
]


# -----------------------------------------------------------------------------
# Workflow Definition Types
# -----------------------------------------------------------------------------


class GateSpec(ExtensionModel):
    """A gate condition for a state transition."""

    type: NonEmptyStr  # Gate type (e.g., 'pr_merged', 'tests_passing')
    required: bool = True
    description: str | None = None
    validator: str | None = None  # Custom validator function name

    @field_validator("required", mode="before")
    @classmethod
    def enforce_required_bool(cls, v: object, info: ValidationInfo) -> object:
        return ensure_strict_bool(v, info, "required")


class DevStateSpec(ExtensionModel):
    """A development lifecycle state."""

    name: NonEmptyStr
    description: str | None = None
    terminal: bool = False
    required_evidence: list[str] = Field(default_factory=list)
    order: NonNegativeInt | None = None  # Maturity order

    @field_validator("terminal", mode="before")
    @classmethod
    def enforce_terminal_bool(cls, v: object, info: ValidationInfo) -> object:
        return ensure_strict_bool(v, info, "terminal")


class DevTransitionSpec(ExtensionModel):
    """A valid state transition with optional gates."""

    from_state: NonEmptyStr
    to_state: NonEmptyStr
    gates: list[GateSpec] = Field(default_factory=list)
    description: str | None = None


class MaturityGate(ExtensionModel):
    """A gate for transitioning between maturity levels.

    Defines what evidence or approvals are required to advance
    an entity from one maturity level to another.
    """

    from_maturity: EntityMaturity = Field(
        description="Source maturity level"
    )
    to_maturity: EntityMaturity = Field(
        description="Target maturity level"
    )
    gates: list[GateSpec] = Field(
        default_factory=list,
        description="Required evidence/approval gates"
    )
    description: str | None = Field(
        default=None,
        description="Human-readable description of this transition"
    )


class EvidenceTypeSpec(ExtensionModel):
    """Custom evidence type definition for a workflow."""

    name: NonEmptyStr  # snake_case identifier
    description: str | None = None
    required_fields: list[
        Literal["reference", "url", "path", "author", "date"]
    ] = Field(default_factory=list)
    reference_pattern: str | None = None  # Regex for validating reference
    url_pattern: str | None = None  # Regex for validating URL


class WorkflowSpec(ExtensionModel):
    """A named workflow defining development lifecycle states and transitions.

    Workflows can define gates in two ways:
    1. State-based (legacy): Using `states` and `transitions` for arbitrary workflow states
    2. Maturity-based: Using `maturity_gates` for EntityMaturity level transitions

    The maturity-based approach is recommended as it aligns with the core
    maturity field on entities.
    """

    name: KebabCaseId  # kebab-case identifier
    description: str | None = None
    # Legacy state-based workflow fields
    states: list[DevStateSpec] = Field(default_factory=list)
    initial_state: NonEmptyStr | None = None
    transitions: list[DevTransitionSpec] = Field(default_factory=list)
    # Maturity-based workflow gates (recommended)
    maturity_gates: list[MaturityGate] = Field(
        default_factory=list,
        description="Gates for maturity level transitions"
    )
    allow_skip: bool = False
    evidence_types: list[EvidenceTypeSpec] = Field(default_factory=list)

    @field_validator("allow_skip", mode="before")
    @classmethod
    def enforce_allow_skip_bool(cls, v: object, info: ValidationInfo) -> object:
        return ensure_strict_bool(v, info, "allow_skip")

    @model_validator(mode="after")
    def validate_workflow(self) -> Self:
        """L005: Validate workflow internal consistency."""
        # Determine workflow mode based on which fields are populated
        has_states = bool(self.states)
        has_maturity_gates = bool(self.maturity_gates)

        # Validate maturity gates mode
        if has_maturity_gates:
            # Maturity gates should have valid progression (can't skip back without reason)
            # This is informational - we don't enforce strict ordering
            pass

        # Validate legacy state-based mode (only if states are defined)
        if has_states:
            state_names = {s.name for s in self.states}
            terminal_states = {s.name for s in self.states if s.terminal}

            # Initial state must be in states (if specified)
            if self.initial_state and self.initial_state not in state_names:
                raise ValueError(
                    f"initial_state '{self.initial_state}' not in defined states"
                )

            # All transition states must be valid
            for t in self.transitions:
                if t.from_state not in state_names:
                    raise ValueError(
                        f"Transition from_state '{t.from_state}' not in defined states"
                    )
                if t.to_state not in state_names:
                    raise ValueError(
                        f"Transition to_state '{t.to_state}' not in defined states"
                    )

            # Check for cycles that don't reach terminal states (potential infinite loops)
            # Build adjacency list
            graph: dict[str, set[str]] = {s.name: set() for s in self.states}
            for t in self.transitions:
                graph[t.from_state].add(t.to_state)

            # Check reachability to terminal states using DFS
            def can_reach_terminal(state: str, visited: set[str]) -> bool:
                if state in terminal_states:
                    return True
                if state in visited:
                    return False  # Cycle detected without reaching terminal
                visited.add(state)
                for next_state in graph[state]:
                    if can_reach_terminal(next_state, visited.copy()):
                        return True
                return False

            # Warn if initial state cannot reach any terminal state
            if self.initial_state and terminal_states and not can_reach_terminal(self.initial_state, set()):
                import warnings
                warnings.warn(
                    f"Workflow '{self.name}': initial state '{self.initial_state}' "
                    "cannot reach any terminal state",
                    UserWarning,
                    stacklevel=2,
                )

        return self


# -----------------------------------------------------------------------------
# Entity Workflow Fields (added to core types when extension is active)
# -----------------------------------------------------------------------------


class WorkflowFields(ExtensionModel):
    """Fields added to entities when workflow extension is active.

    Note: The `maturity` field on core entities is the primary way to track
    development progress. This extension adds workflow orchestration and
    evidence tracking on top of maturity.

    Fields:
        workflow: Optional workflow override for this entity
        maturity_evidence: Evidence supporting current maturity level
        workflow_state: (Legacy) Arbitrary workflow state, use maturity instead
        state_evidence: (Legacy) Alias for maturity_evidence
    """

    workflow: str | None = None  # Workflow override (uses default if not set)
    # Maturity-based evidence (recommended)
    maturity_evidence: Annotated[list[EvidenceSpec], Field()] = Field(default_factory=list)
    # Legacy fields (kept for backward compatibility)
    workflow_state: str | None = Field(
        default=None,
        description="Legacy: use core maturity field instead"
    )
    state_evidence: Annotated[list[EvidenceSpec], Field()] = Field(
        default_factory=list,
        description="Legacy: use maturity_evidence instead"
    )


class WorkflowLibraryFields(ExtensionModel):
    """Fields added to Library when workflow extension is active."""

    workflows: list[WorkflowSpec] = Field(default_factory=list)
    default_workflow: str | None = None


# Ensure forward refs for EvidenceSpec are resolved when imported indirectly
WorkflowFields.model_rebuild()
WorkflowLibraryFields.model_rebuild()
