"""Lint rule implementations."""

# Import rule modules to trigger registration
from libspec.cli.lint.rules import (
    completeness,
    consistency,
    extensions,
    lifecycle,
    naming,
    structural,
    version,
)

__all__ = [
    "structural",
    "naming",
    "completeness",
    "consistency",
    "lifecycle",
    "version",
    "extensions",
]
