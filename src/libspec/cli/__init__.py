"""
libspec CLI: Query and analyze library specifications.

Entry point for the `libspec` command-line tool.
"""

from libspec.cli.app import cli

__all__ = ["cli", "main"]


def main() -> None:
    """Entry point for the libspec CLI."""
    cli()
