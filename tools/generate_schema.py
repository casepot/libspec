"""Generate the core JSON Schema from Pydantic models.

Usage:
    uv run python tools/generate_schema.py          # rewrite core.schema.json
    uv run python tools/generate_schema.py --check  # fail if drift detected

This keeps the schema in sync with the LibspecSpec models, which are the
source of truth for constraints. Extension schemas remain authored in
`src/libspec/schema/extensions/` and are not touched here.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from libspec.models import LibspecSpec

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "src" / "libspec" / "schema" / "core.schema.json"


def generate_schema() -> dict:
    """Return the JSON Schema derived from the models."""

    return LibspecSpec.model_json_schema(by_alias=True)


def main(argv: list[str]) -> int:
    check = "--check" in argv
    schema = generate_schema()

    if check:
        on_disk = json.loads(SCHEMA_PATH.read_text())
        if on_disk != schema:
            sys.stderr.write(
                "core.schema.json is out of date. Run `uv run python tools/generate_schema.py` to update.\n"
            )
            return 1
        return 0

    SCHEMA_PATH.write_text(json.dumps(schema, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
