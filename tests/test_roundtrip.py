import json
from pathlib import Path

import jsonschema

from libspec.models import LibspecSpec

FIXTURES = Path("docs/examples")
CORE_SCHEMA = Path("src/libspec/schema/core.schema.json")


def _load_schema():
    with open(CORE_SCHEMA) as f:
        return json.load(f)


def test_round_trip_validates_minimal_against_schema():
    schema = _load_schema()
    spec_path = FIXTURES / "minimal.json"
    data = json.loads(spec_path.read_text())

    model = LibspecSpec.model_validate(data)
    dumped = model.model_dump(by_alias=True, exclude_none=True)

    jsonschema.validate(instance=dumped, schema=schema)
