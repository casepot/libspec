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
                    "workflow_state": "draft",  # workflow field without extension
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
        "extensions": ["workflow"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "types": [
                {
                    "name": "Greeter",
                    "kind": "class",
                    "module": "mylib",
                    "workflow_state": "stable",
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


def test_async_flags_require_bool_in_strict_mode(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    data = {
        "extensions": ["async"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "types": [
                {
                    "name": "Worker",
                    "kind": "class",
                    "module": "mylib",
                    "methods": [
                        {
                            "name": "run",
                            "signature": "(self) -> None",
                            "async": "yes",
                        }
                    ],
                }
            ],
        },
    }
    spec_path.write_text(json.dumps(data))

    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)

    # lenient mode should still coerce/allow the flag
    load_spec(spec_path, strict=False)


def test_events_retry_limits_positive(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    data = {
        "extensions": ["events"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "events": [{"name": "UserCreated"}],
            "handlers": [
                {
                    "name": "on_user_created",
                    "handles": ["UserCreated"],
                    "function": "handle_user_created",
                    "retry": {"max_attempts": 0},
                }
            ],
        },
    }
    spec_path.write_text(json.dumps(data))

    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)


def test_coverage_paths_checked_in_strict_mode(tmp_path: Path) -> None:
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    target = src_dir / "module.py"
    target.write_text("print('ok')\n")

    spec_path = tmp_path / "spec.json"
    data = {
        "extensions": ["testing"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "coverage": {
                "tool": "coverage.py",
                "targets": [{"path": "src/module.py", "minimum": 80}],
            },
        },
    }
    spec_path.write_text(json.dumps(data))

    load_spec(spec_path, strict=True)

    data["library"]["coverage"]["targets"][0]["path"] = "src/missing.py"
    spec_path.write_text(json.dumps(data))
    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)


def test_perf_benchmarks_require_positive_decimal(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.json"
    data = {
        "extensions": ["perf"],
        "library": {
            "name": "mylib",
            "version": "0.1.0",
            "functions": [
                {
                    "name": "bench",
                    "module": "mylib",
                    "signature": "() -> None",
                    "benchmarks": [{"mean": 0.0}],
                }
            ],
        },
    }
    spec_path.write_text(json.dumps(data))

    with pytest.raises(SpecLoadError):
        load_spec(spec_path, strict=True)

    data["library"]["functions"][0]["benchmarks"][0]["mean"] = 1.23
    spec_path.write_text(json.dumps(data))
    load_spec(spec_path, strict=True)
