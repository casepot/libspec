"""Lint rule implementations."""

# Import rule modules to trigger registration
from libspec.cli.lint.rules import (
    completeness,
    consistency,
    extensions,
    maturity,
    naming,
    structural,
    version,
    workflow,
)

__all__ = [
    "structural",
    "naming",
    "completeness",
    "consistency",
    "maturity",
    "workflow",
    "version",
    "extensions",
]
