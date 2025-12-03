"""Shared validation helpers for libspec models.

These helpers centralize strict-mode awareness and path checks so that
validators can stay small and consistent across models.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from pydantic import DirectoryPath, FilePath, TypeAdapter, ValidationInfo

STRICT_CONTEXT_KEY = "strict_models"
SPEC_DIR_CONTEXT_KEY = "spec_dir"

_PATH_ADAPTER: TypeAdapter[FilePath | DirectoryPath] = TypeAdapter(
    FilePath | DirectoryPath
)


def in_strict_mode(info: ValidationInfo | None) -> bool:
    """Return True when the current validation run is in strict mode."""

    if info is None or info.context is None:
        return False
    return bool(info.context.get(STRICT_CONTEXT_KEY))


def ensure_strict_bool(value: Any, info: ValidationInfo, field: str) -> Any:
    """Enforce that a value is a boolean when strict mode is enabled.

    In non-strict mode the value is returned unchanged so Pydantic's default
    coercion rules still apply, preserving backward compatibility.
    """

    if value is None or not in_strict_mode(info):
        return value
    if isinstance(value, bool):
        return value
    raise TypeError(f"{field} must be a boolean when strict models are enabled")


def validate_local_path(value: str, info: ValidationInfo, field: str) -> str:
    """Validate that a path points to a file or directory when strict.

    - Uses `spec_dir` from validation context as the base for relative paths.
    - Accepts both files and directories to cover test folders and single files.
    - Only performs existence checks in strict mode; otherwise it passes through.
    """

    if not in_strict_mode(info):
        return value

    base_dir = Path(info.context.get(SPEC_DIR_CONTEXT_KEY, Path.cwd())) if info.context else Path.cwd()
    candidate = Path(value)
    probe = candidate if candidate.is_absolute() else base_dir / candidate

    # Use Pydantic's built-in FilePath/DirectoryPath validation for clarity.
    try:
        _PATH_ADAPTER.validate_python(probe)
    except Exception as exc:  # TypeAdapter raises ValidationError
        raise ValueError(f"{field} must reference an existing file or directory: {value}") from exc

    return value


def validate_path_or_url(value: str, info: ValidationInfo, field: str) -> str:
    """Allow URLs; otherwise enforce local path existence in strict mode.

    This validator accepts:
    - HTTP/HTTPS/file:// URLs (passed through without validation)
    - Local file/directory paths (validated in strict mode via validate_local_path)

    Args:
        value: The string to validate (URL or path)
        info: Pydantic validation context
        field: Field name for error messages

    Returns:
        The original value if valid

    Raises:
        ValueError: If strict mode is enabled and path doesn't exist
    """
    if value.startswith(("http://", "https://", "file://")):
        return value
    return validate_local_path(value, info, field)


def validate_regex_pattern(value: str, field: str) -> str:
    """Validate that a string is a valid regular expression pattern.

    Args:
        value: The regex pattern string to validate
        field: Field name for error messages

    Returns:
        The original pattern if valid

    Raises:
        ValueError: If the pattern is not a valid regex
    """
    try:
        re.compile(value)
    except re.error as exc:
        raise ValueError(f"{field} must be a valid regex pattern: {exc}") from exc
    return value

