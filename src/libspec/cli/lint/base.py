"""Base classes for lint rules."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Iterator

from pydantic import BaseModel


class Severity(str, Enum):
    """Lint issue severity levels."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class LintIssue(BaseModel):
    """A single lint issue found in a spec."""

    rule: str
    severity: Severity
    message: str
    path: str  # JSONPath to location
    ref: str | None = None  # libspec cross-reference
    fix_available: bool = False
    suggested_fix: str | None = None


class LintRule(ABC):
    """Base class for all lint rules."""

    id: str  # e.g., "S001"
    name: str  # e.g., "missing-type-description"
    description: str
    default_severity: Severity
    category: str  # structural, naming, completeness, consistency

    @abstractmethod
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        """
        Check the spec for issues.

        Args:
            spec: The loaded spec data
            config: Lint configuration

        Yields:
            LintIssue for each problem found
        """
        pass

    def fix(self, spec: dict[str, Any], issue: LintIssue) -> dict[str, Any] | None:
        """
        Attempt to fix an issue.

        Args:
            spec: The spec data to fix
            issue: The issue to fix

        Returns:
            Fixed spec data, or None if not auto-fixable
        """
        return None

    def get_severity(self, config: dict[str, Any]) -> Severity:
        """Get the severity for this rule, respecting config overrides."""
        rules_config = config.get("rules", {})
        override = rules_config.get(self.id)
        if override:
            if isinstance(override, str):
                try:
                    return Severity(override)
                except ValueError:
                    pass
            elif isinstance(override, dict) and "severity" in override:
                try:
                    return Severity(override["severity"])
                except ValueError:
                    pass
        return self.default_severity
