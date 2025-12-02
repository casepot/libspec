"""Output formatting for CLI commands."""

import json
import sys
from datetime import datetime, timezone
from typing import Any

from libspec.cli.models.output import OutputEnvelope, SpecContext
from libspec.cli.spec_loader import LoadedSpec


def make_envelope(
    command: str,
    spec: LoadedSpec,
    result: Any,
    meta: dict[str, Any] | None = None,
) -> OutputEnvelope[Any]:
    """Create a standard output envelope."""
    return OutputEnvelope(
        command=command,
        spec=SpecContext(
            path=str(spec.path),
            library=spec.name,
            version=spec.version,
        ),
        result=result,
        meta=meta or {},
    )


def output_json(envelope: OutputEnvelope[Any], no_meta: bool = False) -> None:
    """Output envelope as JSON."""
    data = envelope.model_dump(mode="json")
    if no_meta:
        data.pop("meta", None)
    print(json.dumps(data, indent=2))


def output_text_types(types: list[dict[str, Any]]) -> None:
    """Output type list in text format."""
    for t in types:
        kind = t.get("kind", "?")
        name = t.get("name", "?")
        module = t.get("module", "?")
        print(f"TYPE {kind} {name} {module}")
    print("---")
    print(f"{len(types)} types")


def output_text_functions(functions: list[dict[str, Any]]) -> None:
    """Output function list in text format."""
    for f in functions:
        kind = f.get("kind", "function")
        name = f.get("name", "?")
        module = f.get("module", "?")
        print(f"FUNC {kind} {name} {module}")
    print("---")
    print(f"{len(functions)} functions")


def output_text_features(features: list[dict[str, Any]]) -> None:
    """Output feature list in text format."""
    for f in features:
        status = f.get("status", "planned")
        fid = f.get("id", "?")
        category = f.get("category", "?")
        print(f"FEAT {status} {fid} {category}")
    print("---")
    print(f"{len(features)} features")


def output_text_modules(modules: list[dict[str, Any]]) -> None:
    """Output module list in text format."""
    for m in modules:
        path = m.get("path", "?")
        internal = "internal" if m.get("internal") else "public"
        deps = len(m.get("depends_on", []))
        print(f"MOD {internal} {path} deps:{deps}")
    print("---")
    print(f"{len(modules)} modules")


def output_text_principles(principles: list[dict[str, Any]]) -> None:
    """Output principles list in text format."""
    for p in principles:
        pid = p.get("id", "?")
        stmt = p.get("statement", "")[:60]
        print(f"PRINC {pid} {stmt}")
    print("---")
    print(f"{len(principles)} principles")


def output_text_info(
    spec: LoadedSpec,
    counts: dict[str, int],
    coverage: dict[str, Any],
) -> None:
    """Output info in text format."""
    lib = spec.library
    print(f"{lib.get('name', '?')} {lib.get('version', '?')}")
    if spec.extensions:
        print(f"ext: {','.join(spec.extensions)}")
    print(
        f"types: {counts.get('types', 0)} | "
        f"funcs: {counts.get('functions', 0)} | "
        f"features: {counts.get('features', 0)}"
    )
    feat_total = coverage.get("features_total", 0)
    if feat_total > 0:
        tested = coverage.get("features_tested", 0)
        impl = coverage.get("features_implemented", 0)
        print(f"coverage: {impl}/{feat_total} implemented, {tested}/{feat_total} tested")


def output_text_lint(issues: list[dict[str, Any]], passed: bool) -> None:
    """Output lint results in text format."""
    for issue in issues:
        sev = issue.get("severity", "?")[0].upper()  # E/W/I
        rule = issue.get("rule", "?")
        msg = issue.get("message", "")
        path = issue.get("path", "")
        print(f"{sev} {rule} {path} {msg}")
    print("---")
    status = "PASS" if passed else "FAIL"
    print(f"{status} {len(issues)} issues")


def output_text_validate(errors: list[str], valid: bool) -> None:
    """Output validation results in text format."""
    for err in errors:
        print(f"ERR {err}")
    print("---")
    status = "VALID" if valid else "INVALID"
    print(f"{status} {len(errors)} errors")
