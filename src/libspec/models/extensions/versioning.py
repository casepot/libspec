"""Versioning extension models for libspec specifications.

This module defines models for API versioning and deprecation:
- Version constraints and ranges
- Deprecation notices and timelines
- Migration guides and compatibility
"""

from __future__ import annotations

import re
import warnings
from enum import Enum

from pydantic import Field, HttpUrl, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import CrossReference, VersionConstraintStr


def _compare_versions(v1: str, v2: str) -> int:
    """Compare two version strings.

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.
        Returns 0 if versions cannot be compared (non-standard formats).
    """
    # Strip common prefixes like >=, <=, ~=, ==, etc.
    def normalize(v: str) -> str:
        return re.sub(r'^[><=~!]+\\s*', '', v.strip())

    v1_clean = normalize(v1)
    v2_clean = normalize(v2)

    try:
        # Split into numeric parts
        parts1 = [int(x) for x in re.split(r'[.-]', v1_clean) if x.isdigit()]
        parts2 = [int(x) for x in re.split(r'[.-]', v2_clean) if x.isdigit()]

        # Pad to same length
        max_len = max(len(parts1), len(parts2))
        parts1.extend([0] * (max_len - len(parts1)))
        parts2.extend([0] * (max_len - len(parts2)))

        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            if p1 > p2:
                return 1
        return 0
    except (ValueError, AttributeError):
        # Cannot compare non-standard versions, assume OK
        return 0


class Stability(str, Enum):
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

    @model_validator(mode='after')
    def validate_version_ordering(self) -> 'VersioningTypeFields':
        """Validate version ordering: since < deprecated_since < removed_in."""
        if self.since is not None and self.deprecated_since is not None:
            if _compare_versions(self.since, self.deprecated_since) >= 0:
                warnings.warn(
                    f"'since' ({self.since}) should be earlier than "
                    f"'deprecated_since' ({self.deprecated_since})",
                    UserWarning,
                    stacklevel=2,
                )
        if self.deprecated_since is not None and self.removed_in is not None:
            if _compare_versions(self.deprecated_since, self.removed_in) >= 0:
                warnings.warn(
                    f"'deprecated_since' ({self.deprecated_since}) should be earlier than "
                    f"'removed_in' ({self.removed_in})",
                    UserWarning,
                    stacklevel=2,
                )
        return self


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

    @model_validator(mode='after')
    def validate_version_ordering(self) -> 'VersioningMethodFields':
        """Validate version ordering: since < deprecated_since < removed_in."""
        if self.since is not None and self.deprecated_since is not None:
            if _compare_versions(self.since, self.deprecated_since) >= 0:
                warnings.warn(
                    f"'since' ({self.since}) should be earlier than "
                    f"'deprecated_since' ({self.deprecated_since})",
                    UserWarning,
                    stacklevel=2,
                )
        if self.deprecated_since is not None and self.removed_in is not None:
            if _compare_versions(self.deprecated_since, self.removed_in) >= 0:
                warnings.warn(
                    f"'deprecated_since' ({self.deprecated_since}) should be earlier than "
                    f"'removed_in' ({self.removed_in})",
                    UserWarning,
                    stacklevel=2,
                )
        return self


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

    @model_validator(mode='after')
    def validate_version_ordering(self) -> 'DeprecationSpec':
        """Validate since < removed_in."""
        if self.removed_in is not None:
            if _compare_versions(self.since, self.removed_in) >= 0:
                warnings.warn(
                    f"'since' ({self.since}) should be earlier than "
                    f"'removed_in' ({self.removed_in})",
                    UserWarning,
                    stacklevel=2,
                )
        return self


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
    changelog_url: HttpUrl | None = Field(None, description='URL to changelog')
