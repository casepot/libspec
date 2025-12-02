"""Lint-related models."""

from enum import Enum

from pydantic import BaseModel, Field


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


class LintResult(BaseModel):
    """Result of linting a spec."""

    passed: bool
    issues: list[LintIssue] = Field(default_factory=list)


class LintMeta(BaseModel):
    """Metadata about lint results."""

    total: int = 0
    by_severity: dict[str, int] = Field(default_factory=dict)
    by_rule: dict[str, int] = Field(default_factory=dict)
