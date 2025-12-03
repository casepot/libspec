"""
libspec: A schema system for documenting library interfaces.

This package provides JSON Schema definitions for describing:
- Library structure (modules, types, functions)
- Behavioral specifications (features, invariants, contracts)
- Domain-specific extensions (async, web, data, cli, etc.)
- Cross-cutting concerns (errors, performance, safety, etc.)

Usage:
    from libspec import get_schema_path, validate_spec

    # Get path to core schema
    core_schema = get_schema_path("core.schema.json")

    # Validate a spec file
    validate_spec("path/to/libspec.json")

    # Validate with structured errors
    issues = validate_spec("path/to/libspec.json", structured=True)
"""

from copy import deepcopy
from dataclasses import dataclass, field
from enum import Enum
from importlib.resources import files
from pathlib import Path
from typing import Any, Union

__version__ = "0.1.0"

# Schema version this package provides
SCHEMA_VERSION = "1.0"


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""

    ERROR = "error"
    WARNING = "warning"


class ValidationSource(str, Enum):
    """Source of a validation issue."""

    JSON_SCHEMA = "json_schema"
    PYDANTIC = "pydantic"


@dataclass
class ValidationIssue:
    """Structured validation issue with context."""

    message: str
    path: str = "$"
    severity: ValidationSeverity = ValidationSeverity.ERROR
    schema_path: str | None = None
    source: ValidationSource = ValidationSource.JSON_SCHEMA
    context: dict[str, Any] | None = field(default=None)


# Extension names (defined before functions that use them)
DOMAIN_EXTENSIONS = frozenset([
    "async",
    "web",
    "data",
    "cli",
    "orm",
    "testing",
    "events",
    "state",
    "plugins",
    "ml",
    "serialization",
])

CONCERN_EXTENSIONS = frozenset([
    "errors",
    "perf",
    "safety",
    "config",
    "versioning",
    "observability",
    "lifecycle",
])

ALL_EXTENSIONS = DOMAIN_EXTENSIONS | CONCERN_EXTENSIONS


def get_schema_path(schema_name: str = "core.schema.json") -> Path:
    """
    Get the filesystem path to a schema file.

    Args:
        schema_name: Name of the schema file (e.g., "core.schema.json" or
                     "extensions/async.schema.json")

    Returns:
        Path to the schema file

    Raises:
        FileNotFoundError: If the schema file doesn't exist
    """
    schema_dir = files("libspec") / "schema"
    schema_path = Path(str(schema_dir / schema_name))
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_name}")
    return schema_path


def get_core_schema() -> dict[str, Any]:
    """
    Load and return the core schema as a dictionary.

    Returns:
        The core JSON Schema as a dict
    """
    import json

    schema_path = get_schema_path("core.schema.json")
    with open(schema_path) as f:
        return json.load(f)


def get_extension_schema(extension_name: str) -> dict[str, Any]:
    """
    Load an extension schema by name.

    Args:
        extension_name: Name of the extension (e.g., "async", "web", "errors")

    Returns:
        The extension JSON Schema as a dict

    Raises:
        ValueError: If the extension name is not recognized
        FileNotFoundError: If the extension schema file doesn't exist
    """
    import json

    if extension_name not in ALL_EXTENSIONS:
        raise ValueError(
            f"Unknown extension: {extension_name!r}. "
            f"Valid extensions: {sorted(ALL_EXTENSIONS)}"
        )

    schema_path = get_schema_path(f"extensions/{extension_name}.schema.json")
    with open(schema_path) as f:
        return json.load(f)


def merge_schemas(
    core_schema: dict[str, Any], extension_names: list[str]
) -> tuple[dict[str, Any], list[ValidationIssue]]:
    """
    Merge core schema with extension schemas.

    This performs a deep merge of $defs from each extension schema into
    the core schema, allowing validation of extension-specific fields.

    Args:
        core_schema: The core libspec schema
        extension_names: List of extension names to merge

    Returns:
        Tuple of (merged_schema, warnings) where warnings contains any
        issues encountered during merging (e.g., unknown extensions)
    """
    merged = deepcopy(core_schema)
    warnings: list[ValidationIssue] = []

    # Ensure $defs exists
    if "$defs" not in merged:
        merged["$defs"] = {}

    for ext_name in extension_names:
        if ext_name not in ALL_EXTENSIONS:
            warnings.append(
                ValidationIssue(
                    message=f"Unknown extension: {ext_name!r}",
                    path="$.extensions",
                    severity=ValidationSeverity.WARNING,
                    context={"extension": ext_name, "valid": sorted(ALL_EXTENSIONS)},
                )
            )
            continue

        try:
            ext_schema = get_extension_schema(ext_name)
        except FileNotFoundError:
            warnings.append(
                ValidationIssue(
                    message=f"Extension schema not found: {ext_name}",
                    path="$.extensions",
                    severity=ValidationSeverity.WARNING,
                    context={"extension": ext_name},
                )
            )
            continue

        # Merge $defs from extension into core
        if "$defs" in ext_schema:
            for def_name, def_schema in ext_schema["$defs"].items():
                if def_name in merged["$defs"]:
                    # Skip if already defined (core takes precedence)
                    continue
                merged["$defs"][def_name] = def_schema

    return merged, warnings


def validate_spec(
    spec_path: Union[str, Path],
    *,
    structured: bool = False,
) -> Union[list[str], list[ValidationIssue]]:
    """
    Validate a libspec specification file against the schema.

    Automatically detects and merges extension schemas based on the
    "extensions" field in the spec.

    Args:
        spec_path: Path to the specification file to validate
        structured: If True, return ValidationIssue objects instead of strings

    Returns:
        List of validation errors (empty if valid). If structured=True,
        returns ValidationIssue objects with full context.
    """
    import json

    from jsonschema import Draft202012Validator

    spec_path = Path(spec_path)
    with open(spec_path) as f:
        spec = json.load(f)

    # Start with core schema
    schema = get_core_schema()
    issues: list[ValidationIssue] = []

    # Merge extension schemas based on spec["extensions"]
    extensions = spec.get("extensions", [])
    if extensions:
        schema, merge_warnings = merge_schemas(schema, extensions)
        issues.extend(merge_warnings)

    # Validate with JSON Schema
    validator = Draft202012Validator(schema)
    for error in validator.iter_errors(spec):
        path = "$" + "".join(
            f"[{p!r}]" if isinstance(p, str) else f"[{p}]" for p in error.absolute_path
        )
        issues.append(
            ValidationIssue(
                message=error.message,
                path=path,
                severity=ValidationSeverity.ERROR,
                schema_path=error.json_path if hasattr(error, "json_path") else None,
                source=ValidationSource.JSON_SCHEMA,
            )
        )

    # Also validate with Pydantic to catch model validators
    # Only run if JSON Schema validation passed (to avoid duplicate errors)
    if not any(issue.severity == ValidationSeverity.ERROR for issue in issues):
        from pydantic import ValidationError

        from libspec.models.core import LibspecSpec

        try:
            LibspecSpec.model_validate(spec)
        except ValidationError as e:
            for err in e.errors():
                # Format the path from Pydantic's loc tuple
                loc_parts = []
                for part in err["loc"]:
                    if isinstance(part, int):
                        loc_parts.append(f"[{part}]")
                    else:
                        loc_parts.append(f"[{part!r}]")
                path = "$" + "".join(loc_parts)

                issues.append(
                    ValidationIssue(
                        message=err["msg"],
                        path=path,
                        severity=ValidationSeverity.ERROR,
                        source=ValidationSource.PYDANTIC,
                        context={"type": err["type"]},
                    )
                )

    if structured:
        return issues
    return [issue.message for issue in issues if issue.severity == ValidationSeverity.ERROR]
