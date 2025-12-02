"""Lifecycle extension models for development workflow tracking.

This extension provides:
- Workflow definitions with states and transitions
- Evidence types for tracking progress (PRs, tests, docs, etc.)
- Lifecycle state fields for entities (types, functions, features)
"""

from __future__ import annotations

import re
from typing import Annotated, Literal, Union

from pydantic import Field, AnyUrl, conlist, field_validator, model_validator
from typing_extensions import Self

from ..base import ExtensionModel

# -----------------------------------------------------------------------------
# Evidence Types (Discriminated Union Members)
# -----------------------------------------------------------------------------


class EvidenceBase(ExtensionModel):
    """Base fields shared by all evidence types."""

    description: str | None = None
    date: str | None = None  # ISO date format


class PrEvidence(EvidenceBase):
    """Pull/merge request evidence."""

    type: Literal["pr"]
    url: AnyUrl  # URL to the PR
    author: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """L006: Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"PR URL must be http/https: {v}")
        return v


class TestsEvidence(EvidenceBase):
    """Test file/directory evidence."""

    type: Literal["tests"]
    path: str

    @field_validator("path")
    @classmethod
    def validate_test_path(cls, v: str) -> str:
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
        return v


class DesignDocEvidence(EvidenceBase):
    """Design document evidence."""

    type: Literal["design_doc"]
    reference: str  # URL or path to design doc
    author: str | None = None


class DocsEvidence(EvidenceBase):
    """Documentation URL evidence."""

    type: Literal["docs"]
    url: AnyUrl

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """L006: Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError(f"Docs URL must be http/https: {v}")
        return v


class ApprovalEvidence(EvidenceBase):
    """Approval evidence - requires author."""

    type: Literal["approval"]
    reference: str
    author: str  # Required for approvals


class BenchmarkEvidence(EvidenceBase):
    """Benchmark results evidence."""

    type: Literal["benchmark"]
    reference: str
    metrics: dict[str, int | float | str] = Field(default_factory=dict)
    author: str | None = None


class MigrationGuideEvidence(EvidenceBase):
    """Migration guide evidence."""

    type: Literal["migration_guide"]
    reference: str


class DeprecationNoticeEvidence(EvidenceBase):
    """Deprecation notice evidence - requires date."""

    type: Literal["deprecation_notice"]
    reference: str
    date: str  # Required for deprecation notices


class CustomEvidence(EvidenceBase):
    """Custom evidence type defined in workflow."""

    type: Literal["custom"]
    type_name: str  # References workflow evidence_types
    reference: str | None = None
    url: AnyUrl | None = None
    path: str | None = None
    author: str | None = None


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

    type: str  # Gate type (e.g., 'pr_merged', 'tests_passing')
    required: bool = True
    description: str | None = None
    validator: str | None = None  # Custom validator function name


class DevStateSpec(ExtensionModel):
    """A development lifecycle state."""

    name: str
    description: str | None = None
    terminal: bool = False
    required_evidence: list[str] = Field(default_factory=list)
    order: int | None = None  # Maturity order


class DevTransitionSpec(ExtensionModel):
    """A valid state transition with optional gates."""

    from_state: str
    to_state: str
    gates: list[GateSpec] = Field(default_factory=list)
    description: str | None = None


class EvidenceTypeSpec(ExtensionModel):
    """Custom evidence type definition for a workflow."""

    name: str  # snake_case identifier
    description: str | None = None
    required_fields: list[
        Literal["reference", "url", "path", "author", "date"]
    ] = Field(default_factory=list)
    reference_pattern: str | None = None  # Regex for validating reference
    url_pattern: str | None = None  # Regex for validating URL


class WorkflowSpec(ExtensionModel):
    """A named workflow defining development lifecycle states and transitions."""

    name: str  # kebab-case identifier
    description: str | None = None
    states: list[DevStateSpec] = Field(min_length=1)
    initial_state: str
    transitions: list[DevTransitionSpec] = Field(default_factory=list)
    allow_skip: bool = False
    evidence_types: list[EvidenceTypeSpec] = Field(default_factory=list)

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
    state_evidence: conlist(EvidenceSpec, min_length=1) = Field(default_factory=list)


class LifecycleLibraryFields(ExtensionModel):
    """Fields added to Library when lifecycle extension is active."""

    workflows: list[WorkflowSpec] = Field(default_factory=list)
    default_workflow: str | None = None
