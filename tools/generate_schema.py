"""Generate JSON Schemas from Pydantic models.

Usage:
    uv run python tools/generate_schema.py            # regenerate all schemas
    uv run python tools/generate_schema.py --check    # fail if drift detected
    uv run python tools/generate_schema.py --verbose  # show status of each schema

This generates:
- core.schema.json from LibspecSpec model
- extensions/*.schema.json from extension models

The Pydantic models are the single source of truth. Never edit JSON schemas directly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from libspec.models import LibspecSpec
from libspec.models.extensions import async_ as async_ext
from libspec.models.extensions import cli as cli_ext
from libspec.models.extensions import config as config_ext
from libspec.models.extensions import data as data_ext
from libspec.models.extensions import errors as errors_ext
from libspec.models.extensions import events as events_ext
from libspec.models.extensions import lifecycle as lifecycle_ext
from libspec.models.extensions import observability as observability_ext
from libspec.models.extensions import orm as orm_ext
from libspec.models.extensions import perf as perf_ext
from libspec.models.extensions import plugins as plugins_ext
from libspec.models.extensions import safety as safety_ext
from libspec.models.extensions import serialization as serialization_ext
from libspec.models.extensions import state as state_ext
from libspec.models.extensions import testing as testing_ext
from libspec.models.extensions import versioning as versioning_ext
from libspec.models.extensions import web as web_ext

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "src" / "libspec" / "schema"
CORE_SCHEMA_PATH = SCHEMA_DIR / "core.schema.json"
EXTENSIONS_DIR = SCHEMA_DIR / "extensions"

# Extension metadata and root models
# Each extension maps to: (title, description, list of root model classes)
EXTENSIONS: dict[str, tuple[str, str, list[type]]] = {
    "async": (
        "Async Extension",
        "Extension for async/concurrent system semantics: lifecycle, cancellation, synchronization, observables.",
        [
            async_ext.AsyncMethodFields,
            async_ext.AsyncFunctionFields,
            async_ext.AsyncTypeFields,
        ],
    ),
    "cli": (
        "CLI Extension",
        "Extension for command-line interface specifications.",
        [cli_ext.CLILibraryFields],
    ),
    "config": (
        "Config Extension",
        "Extension for configuration management specifications.",
        [config_ext.ConfigLibraryFields],
    ),
    "data": (
        "Data Extension",
        "Extension for data processing and transformation specifications.",
        [
            data_ext.DataLibraryFields,
            data_ext.DataMethodFields,
            data_ext.DataTypeFields,
        ],
    ),
    "errors": (
        "Errors Extension",
        "Extension for error handling and exception specifications.",
        [errors_ext.ErrorsLibraryFields],
    ),
    "events": (
        "Events Extension",
        "Extension for event-driven architecture specifications.",
        [
            events_ext.EventsLibraryFields,
            events_ext.EventsMethodFields,
            events_ext.EventsTypeFields,
        ],
    ),
    "lifecycle": (
        "Lifecycle Extension",
        "Extension for development lifecycle tracking: states, transitions, evidence, workflows.",
        [
            lifecycle_ext.LifecycleFields,
            lifecycle_ext.LifecycleLibraryFields,
        ],
    ),
    "observability": (
        "Observability Extension",
        "Extension for logging, metrics, and tracing specifications.",
        [observability_ext.ObservabilityLibraryFields],
    ),
    "orm": (
        "ORM Extension",
        "Extension for object-relational mapping specifications.",
        [orm_ext.ORMLibraryFields],
    ),
    "perf": (
        "Performance Extension",
        "Extension for performance characteristics and constraints.",
        [
            perf_ext.PerfFunctionFields,
            perf_ext.PerfMethodFields,
            perf_ext.PerfTypeFields,
        ],
    ),
    "plugins": (
        "Plugins Extension",
        "Extension for plugin system specifications.",
        [
            plugins_ext.PluginsLibraryFields,
            plugins_ext.PluginsTypeFields,
        ],
    ),
    "safety": (
        "Safety Extension",
        "Extension for thread safety and concurrency guarantees.",
        [
            safety_ext.SafetyFunctionFields,
            safety_ext.SafetyMethodFields,
            safety_ext.SafetyTypeFields,
        ],
    ),
    "serialization": (
        "Serialization Extension",
        "Extension for data serialization: formats, encoders/decoders, type coercion, schemas.",
        [
            serialization_ext.SerializationLibraryFields,
            serialization_ext.SerializationTypeFields,
            serialization_ext.SerializationMethodFields,
            serialization_ext.SerializationFunctionFields,
        ],
    ),
    "state": (
        "State Extension",
        "Extension for state management specifications.",
        [
            state_ext.StateLibraryFields,
            state_ext.StateTypeFields,
        ],
    ),
    "testing": (
        "Testing Extension",
        "Extension for testing utilities: fixtures, mocks, test patterns, assertions.",
        [
            testing_ext.TestingLibraryFields,
            testing_ext.TestingTypeFields,
        ],
    ),
    "versioning": (
        "Versioning Extension",
        "Extension for API versioning and deprecation specifications.",
        [
            versioning_ext.VersioningLibraryFields,
            versioning_ext.VersioningMethodFields,
            versioning_ext.VersioningTypeFields,
        ],
    ),
    "web": (
        "Web Extension",
        "Extension for web framework specifications.",
        [web_ext.WebLibraryFields],
    ),
}


def generate_core_schema() -> dict[str, Any]:
    """Return the JSON Schema derived from the core models."""
    return LibspecSpec.model_json_schema(by_alias=True, mode="validation")


def generate_extension_schema(
    name: str, title: str, description: str, models: list[type]
) -> dict[str, Any]:
    """Generate a JSON Schema for an extension from its Pydantic models.

    Args:
        name: Extension name (e.g., "async", "testing")
        title: Human-readable title
        description: Extension description
        models: List of root model classes for this extension

    Returns:
        JSON Schema dict with combined $defs from all models
    """
    # Collect all $defs from all models
    all_defs: dict[str, Any] = {}

    for model in models:
        # Generate schema for this model
        adapter = TypeAdapter(model)
        schema = adapter.json_schema(by_alias=True, mode="validation")

        # Extract $defs if present
        if "$defs" in schema:
            all_defs.update(schema["$defs"])

        # The model itself should be in $defs too
        model_name = model.__name__
        model_schema = {k: v for k, v in schema.items() if k != "$defs"}
        if model_schema:
            all_defs[model_name] = model_schema

    # Build the final schema
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://libspec.dev/schema/1.0/extensions/{name}.schema.json",
        "title": title,
        "description": description,
        "$defs": all_defs,
    }


def write_schema(path: Path, schema: dict[str, Any]) -> None:
    """Write a schema to disk with consistent formatting."""
    path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")


def check_schema(path: Path, schema: dict[str, Any]) -> bool:
    """Check if the on-disk schema matches the generated one."""
    if not path.exists():
        return False
    on_disk = json.loads(path.read_text())
    return on_disk == schema


def main(argv: list[str]) -> int:
    check = "--check" in argv
    verbose = "--verbose" in argv or "-v" in argv
    errors: list[str] = []

    # Generate core schema
    core_schema = generate_core_schema()
    if check:
        is_ok = check_schema(CORE_SCHEMA_PATH, core_schema)
        if verbose:
            status = "✓ up-to-date" if is_ok else "✗ drift detected"
            print(f"  core.schema.json: {status}")
        if not is_ok:
            errors.append("core.schema.json")
    else:
        write_schema(CORE_SCHEMA_PATH, core_schema)
        if verbose:
            print(f"  core.schema.json: ✓ written")

    # Generate extension schemas
    for ext_name, (title, description, models) in sorted(EXTENSIONS.items()):
        ext_schema = generate_extension_schema(ext_name, title, description, models)
        ext_path = EXTENSIONS_DIR / f"{ext_name}.schema.json"

        if check:
            is_ok = check_schema(ext_path, ext_schema)
            if verbose:
                status = "✓ up-to-date" if is_ok else "✗ drift detected"
                print(f"  extensions/{ext_name}.schema.json: {status}")
            if not is_ok:
                errors.append(f"extensions/{ext_name}.schema.json")
        else:
            write_schema(ext_path, ext_schema)
            if verbose:
                print(f"  extensions/{ext_name}.schema.json: ✓ written")

    if errors:
        sys.stderr.write(
            f"\nThe following schemas are out of date: {', '.join(errors)}\n"
            "Run `uv run python tools/generate_schema.py` to update.\n"
        )
        return 1

    if check and verbose:
        print(f"\nAll {1 + len(EXTENSIONS)} schemas are up-to-date.")
    elif not check:
        print(f"Generated core.schema.json and {len(EXTENSIONS)} extension schemas.")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
