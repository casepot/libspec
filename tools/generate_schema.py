#!/usr/bin/env python3
"""Generate JSON Schema from Pydantic models.

This script generates JSON Schema files from the Pydantic models defined in
libspec.models. The generated schemas replace the manually-maintained schema
files.

Usage:
    # Generate schemas to src/libspec/schema/
    uv run python tools/generate_schema.py

    # Check for drift (CI mode)
    uv run python tools/generate_schema.py --check

    # Generate to a different directory
    uv run python tools/generate_schema.py --output-dir /tmp/schemas
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from libspec.models import LibspecSpec

# Type alias for JSON schema dict
JsonSchema = dict[str, Any]


def generate_core_schema() -> JsonSchema:
    """Generate the core JSON schema from LibspecSpec model."""
    schema = LibspecSpec.model_json_schema(
        mode="validation",
        ref_template="#/$defs/{model}",
    )

    # Add schema metadata
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://libspec.dev/schema/core.schema.json"
    schema["title"] = "LibSpec Core Schema"
    schema["description"] = (
        "Schema for library specification documents (generated from Pydantic models)"
    )

    return schema


def write_schema(schema: JsonSchema, path: Path) -> None:
    """Write schema to a JSON file with consistent formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(schema, f, indent=2, sort_keys=False)
        f.write("\n")  # Trailing newline


def read_existing_schema(path: Path) -> JsonSchema | None:
    """Read an existing schema file, returning None if it doesn't exist."""
    if not path.exists():
        return None
    with open(path) as f:
        data: JsonSchema = json.load(f)
        return data


def schemas_match(generated: JsonSchema, existing: JsonSchema | None) -> bool:
    """Check if generated schema matches existing schema."""
    if existing is None:
        return False
    # Compare as JSON strings to handle ordering differences
    gen_str = json.dumps(generated, indent=2, sort_keys=True)
    exist_str = json.dumps(existing, indent=2, sort_keys=True)
    return gen_str == exist_str


def show_diff(generated: JsonSchema, existing: JsonSchema | None, path: Path) -> None:
    """Show diff between generated and existing schema."""
    gen_lines = json.dumps(generated, indent=2, sort_keys=True).splitlines(keepends=True)
    if existing is None:
        print(f"\n{path} does not exist (would be created)")
        return

    exist_lines = json.dumps(existing, indent=2, sort_keys=True).splitlines(keepends=True)
    diff = list(difflib.unified_diff(
        exist_lines,
        gen_lines,
        fromfile=f"existing/{path.name}",
        tofile=f"generated/{path.name}",
    ))
    if diff:
        print(f"\nDiff for {path}:")
        for line in diff:
            print(line, end="")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate JSON Schema from Pydantic models"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check for drift without writing (exits non-zero if different)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent.parent / "src" / "libspec" / "schema",
        help="Output directory for generated schemas",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show diffs in check mode",
    )

    args = parser.parse_args()

    # Generate schemas
    core_schema = generate_core_schema()
    core_path = args.output_dir / "core.schema.json"

    schemas = [
        (core_schema, core_path),
    ]

    if args.check:
        # Check mode: verify schemas match
        all_match = True
        for schema, path in schemas:
            existing = read_existing_schema(path)
            if not schemas_match(schema, existing):
                all_match = False
                print(f"Schema drift detected: {path}")
                if args.verbose:
                    show_diff(schema, existing, path)

        if not all_match:
            print("\nRun 'uv run python tools/generate_schema.py' to regenerate schemas")
            return 1

        print("All schemas up to date")
        return 0

    # Write mode: generate schemas
    for schema, path in schemas:
        write_schema(schema, path)
        print(f"Generated {path}")

    print(f"\nGenerated {len(schemas)} schema file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
