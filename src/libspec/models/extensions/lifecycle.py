"""Lifecycle extension models for development workflow tracking.

This extension provides:
- Workflow definitions with states and transitions
- Evidence types for tracking progress (PRs, tests, docs, etc.)
- Lifecycle state fields for entities (types, functions, features)
"""

from __future__ import annotations

import re
from datetime import date as date_type
from typing import Annotated, Literal, Union

from pydantic import (
    AnyUrl,
    Field,
    HttpUrl,
    NonNegativeInt,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from ..base import ExtensionModel
from ..types import KebabCaseId, NonEmptyStr
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
    url: HttpUrl | None  # URL to the PR
    author: str | None = None


class TestsEvidence(EvidenceBase):
    """Test file/directory evidence."""

    type: Literal["tests"]
    path: NonEmptyStr

    @field_validator("path")
    @classmethod
    def validate_test_path(cls, v: str, info: ValidationInfo) -> str:
        """L009: Validate test path looks like a test file."""
        # Common test file patterns
        patterns = [
            r"test_.*\.py$",
            r".*_test\.py$",
            r"tests?/",
            r"spec/",
            r".*\.spec\.(ts|js)$",
            r".*\.test\.(ts|js)$",
        ]
        if not any(re.search(p, v) for p in patterns):
            raise ValueError(f"Path does not look like a test file: {v}")
        return validate_local_path(v, info, "path")


class DesignDocEvidence(EvidenceBase):
    """Design document evidence."""

    type: Literal["design_doc"]
    reference: NonEmptyStr  # URL or path to design doc
    author: str | None = None

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str, info: ValidationInfo) -> str:
        return validate_path_or_url(v, info, "reference")


class DocsEvidence(EvidenceBase):
    """Documentation URL evidence."""

    type: Literal["docs"]
    url: HttpUrl | None


class ApprovalEvidence(EvidenceBase):
    """Approval evidence - requires author."""

    type: Literal["approval"]
    reference: NonEmptyStr
    author: NonEmptyStr  # Required for approvals


class BenchmarkEvidence(EvidenceBase):
    """Benchmark results evidence."""

    type: Literal["benchmark"]
    reference: NonEmptyStr
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    author: str | None = None

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str, info: ValidationInfo) -> str:
        return validate_path_or_url(v, info, "reference")


class MigrationGuideEvidence(EvidenceBase):
    """Migration guide evidence."""

    type: Literal["migration_guide"]
    reference: NonEmptyStr

    @field_validator("reference")
    @classmethod
    def validate_reference(cls, v: str, info: ValidationInfo) -> str:
        return validate_path_or_url(v, info, "reference")


class DeprecationNoticeEvidence(EvidenceBase):
    """Deprecation notice evidence - requires date."""

    type: Literal["deprecation_notice"]
    reference: NonEmptyStr
    date: date_type = Field(..., description="Date of the deprecation notice")  # type: ignore[assignment]  # Required - valid Pydantic pattern


class CustomEvidence(EvidenceBase):
    """Custom evidence type defined in workflow."""

    type: Literal["custom"]
    type_name: NonEmptyStr  # References workflow evidence_types
    reference: str | None = None
    url: AnyUrl | None = None
    path: str | None = None
    author: str | None = None

    @field_validator("path")
    @classmethod
    def validate_optional_path(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            return None
        return validate_local_path(v, info, "path")

    @field_validator("reference")
    @classmethod
    def validate_optional_reference(cls, v: str | None, info: ValidationInfo) -> str | None:
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
    """A named workflow defining development lifecycle states and transitions."""

    name: KebabCaseId  # kebab-case identifier
    description: str | None = None
    states: list[DevStateSpec] = Field(min_length=1)
    initial_state: NonEmptyStr
    transitions: list[DevTransitionSpec] = Field(default_factory=list)
    allow_skip: bool = False
    evidence_types: list[EvidenceTypeSpec] = Field(default_factory=list)

    @field_validator("allow_skip", mode="before")
    @classmethod
    def enforce_allow_skip_bool(cls, v: object, info: ValidationInfo) -> object:
        return ensure_strict_bool(v, info, "allow_skip")

    @model_validator(mode="after")
    def validate_workflow(self) -> Self:
        """L005: Validate workflow internal consistency."""
        state_names = {s.name for s in self.states}

        # Initial state must be in states
        if self.initial_state not in state_names:
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

        return self


# -----------------------------------------------------------------------------
# Entity Lifecycle Fields (added to core types when extension is active)
# -----------------------------------------------------------------------------


class LifecycleFields(ExtensionModel):
    """Fields added to entities when lifecycle extension is active."""

    lifecycle_state: str | None = None
    workflow: str | None = None  # Workflow override (uses default if not set)
    state_evidence: Annotated[list[EvidenceSpec], Field(min_length=1)] = Field(default_factory=list)


class LifecycleLibraryFields(ExtensionModel):
    """Fields added to Library when lifecycle extension is active."""

    workflows: list[WorkflowSpec] = Field(default_factory=list)
    default_workflow: str | None = None


# Ensure forward refs for EvidenceSpec are resolved when imported indirectly
LifecycleFields.model_rebuild()
LifecycleLibraryFields.model_rebuild()
