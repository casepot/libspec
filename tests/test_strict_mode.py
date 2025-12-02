from pathlib import Path

import json
import pytest

from libspec.cli.spec_loader import SpecLoadError, load_spec
from libspec.models import FunctionDef, Library, LibspecSpec


def test_extension_field_rejected_without_declaration(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    data = {
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "features": [
                {
                    "id": "feat",
                    "category": "CORE",
                    "steps": ["step"],
                    "lifecycle_state": "draft",  # lifecycle field without extension
                }
            ],
        }
    }
    spec_path.write_text(json.dumps(data))

    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)


def test_test_path_must_exist_in_strict_mode(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_example.py").write_text("pass\n")

    spec_path = tmp_path / "spec.json"
    data = {
        "extensions": ["lifecycle"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "types": [
                {
                    "name": "Greeter",
                    "kind": "class",
                    "module": "mylib",
                    "lifecycle_state": "stable",
                    "state_evidence": [
                        {"type": "tests", "path": "tests/test_example.py"}
                    ],
                    "methods": [
                        {
                            "name": "greet",
                            "signature": "(self) -> None",
                            "description": "greet",
                        }
                    ],
                }
            ],
        },
    }
    spec_path.write_text(json.dumps(data))

    load_spec(spec_path, strict=True)

    # Now point to a missing path and expect failure
    data["library"]["types"][0]["state_evidence"][0]["path"] = "tests/missing.py"
    spec_path.write_text(json.dumps(data))
    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)


def test_strict_bool_flags_not_coerced() -> None:
    with pytest.raises(Exception):
        FunctionDef.model_validate(
            {
                "name": "func",
                "module": "mylib",
                "signature": "() -> None",
                "idempotent": "yes",
            },
            strict=True,
        )

    # Non-strict should coerce
    fn = FunctionDef.model_validate(
        {
            "name": "func",
            "module": "mylib",
            "signature": "() -> None",
            "idempotent": 1,
        },
        strict=False,
    )
    assert fn.idempotent is True


def test_non_empty_parameter_name() -> None:
    with pytest.raises(Exception):
        FunctionDef.model_validate(
            {
                "name": "func",
                "module": "mylib",
                "signature": "() -> None",
                "parameters": [{"name": "", "kind": "positional_or_keyword"}],
            }
        )
