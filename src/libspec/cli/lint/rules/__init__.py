"""Lint rule implementations."""

# Import rule modules to trigger registration
from libspec.cli.lint.rules import completeness, consistency, lifecycle, naming, structural

__all__ = ["structural", "naming", "completeness", "consistency", "lifecycle"]
