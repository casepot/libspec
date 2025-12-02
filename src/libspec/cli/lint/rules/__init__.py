"""Lint rule implementations."""

# Import rule modules to trigger registration
from libspec.cli.lint.rules import structural
from libspec.cli.lint.rules import naming
from libspec.cli.lint.rules import completeness
from libspec.cli.lint.rules import consistency

__all__ = ["structural", "naming", "completeness", "consistency"]
