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
"""

from importlib.resources import files
from pathlib import Path
from typing import Union

__version__ = "0.1.0"

# Schema version this package provides
SCHEMA_VERSION = "1.0"


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


def get_core_schema() -> dict:
    """
    Load and return the core schema as a dictionary.

    Returns:
        The core JSON Schema as a dict
    """
    import json
    schema_path = get_schema_path("core.schema.json")
    with open(schema_path) as f:
        return json.load(f)


def validate_spec(spec_path: Union[str, Path]) -> list[str]:
    """
    Validate a libspec specification file against the schema.

    Args:
        spec_path: Path to the specification file to validate

    Returns:
        List of validation errors (empty if valid)
    """
    import json
    from jsonschema import Draft202012Validator

    spec_path = Path(spec_path)
    with open(spec_path) as f:
        spec = json.load(f)

    # Determine which schema to use based on extensions
    schema = get_core_schema()

    # TODO: Merge extension schemas based on spec["extensions"]

    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(spec))
    return [str(e.message) for e in errors]


# Extension names
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
])

CONCERN_EXTENSIONS = frozenset([
    "errors",
    "perf",
    "safety",
    "config",
    "versioning",
    "observability",
])

ALL_EXTENSIONS = DOMAIN_EXTENSIONS | CONCERN_EXTENSIONS
