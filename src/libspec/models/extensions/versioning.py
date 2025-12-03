"""Versioning extension models for libspec specifications.

This module defines models for API versioning and deprecation:
- Version constraints and ranges
- Deprecation notices and timelines
- Migration guides and compatibility
"""

from __future__ import annotations

from enum import Enum

from pydantic import AnyUrl, Field

from libspec.models.base import ExtensionModel
from libspec.models.types import CrossReference, VersionConstraintStr


class Stability(Enum):
    """API stability level indicating maturity and change likelihood.

    - stable: Production-ready, backward-compatible changes only
    - beta: Feature-complete but may have minor changes
    - alpha: Early development, API may change significantly
    - experimental: Highly unstable, may be removed
    - deprecated: Scheduled for removal, use replacement
    """

    stable = 'stable'
    beta = 'beta'
    alpha = 'alpha'
    experimental = 'experimental'
    deprecated = 'deprecated'


class VersioningTypeFields(ExtensionModel):
    since: VersionConstraintStr | None = Field(
        None, description='Version when this type was introduced'
    )
    deprecated_since: VersionConstraintStr | None = Field(
        None, description='Version when this type was deprecated'
    )
    removed_in: VersionConstraintStr | None = Field(
        None, description='Version when this type will be/was removed'
    )
    stability: Stability | None = None


class VersioningMethodFields(ExtensionModel):
    since: VersionConstraintStr | None = Field(
        None, description='Version when this method was introduced'
    )
    deprecated_since: VersionConstraintStr | None = Field(
        None, description='Version when this method was deprecated'
    )
    removed_in: VersionConstraintStr | None = Field(
        None, description='Version when this method will be/was removed'
    )
    stability: Stability | None = None


class DeprecationSpec(ExtensionModel):
    target: CrossReference = Field(
        default=..., description='What is deprecated (cross-reference)'
    )
    since: VersionConstraintStr = Field(default=..., description='Version when deprecated')
    removed_in: VersionConstraintStr | None = Field(
        None, description='Version when removed (or planned removal)'
    )
    replacement: CrossReference | None = Field(
        None, description='What to use instead (cross-reference)'
    )
    migration: str | None = Field(None, description='Migration instructions')
    reason: str | None = Field(None, description='Why this was deprecated')


class BreakingChangeSpec(ExtensionModel):
    version: VersionConstraintStr = Field(
        default=..., description='Version containing the breaking change'
    )
    change: str = Field(default=..., description='Description of what changed')
    affected: list[CrossReference] | None = Field(
        None, description='Affected APIs (cross-references)'
    )
    migration: str | None = Field(None, description='Migration instructions')
    automated_fix: bool | None = Field(
        False, description='Whether an automated fix is available'
    )
    codemod: str | None = Field(None, description='Codemod command to apply fix')


class SemVerPolicySpec(ExtensionModel):
    major: str | None = Field(None, description='What constitutes a major version bump')
    minor: str | None = Field(None, description='What constitutes a minor version bump')
    patch: str | None = Field(None, description='What constitutes a patch version bump')


class CompatibilitySpec(ExtensionModel):
    backward: str | None = Field(
        None, description="Backward compatibility scope (e.g., '2.x series')"
    )
    forward: bool | None = Field(
        None, description='Whether forward compatibility is maintained'
    )
    policy: str | None = Field(None, description='Compatibility policy description')
    semantic_versioning: SemVerPolicySpec | None = None


class VersioningLibraryFields(ExtensionModel):
    api_version: str | None = Field(
        None, description='API version (may differ from package version)'
    )
    stability: Stability | None = Field(None, description='API stability level')
    deprecations: list[DeprecationSpec] | None = Field(
        None, description='Deprecated APIs'
    )
    breaking_changes: list[BreakingChangeSpec] | None = Field(
        None, description='Breaking changes by version'
    )
    compatibility: CompatibilitySpec | None = None
    changelog_url: AnyUrl | None = Field(None, description='URL to changelog')
