"""Consistency lint rules (X001-X099)."""

from typing import Any, Iterator

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


def collect_valid_refs(spec: dict[str, Any]) -> set[str]:
    """Collect all valid cross-references in a spec."""
    refs = set()
    library = spec.get("library", {})

    # Types
    for type_def in library.get("types", []):
        name = type_def.get("name")
        if name:
            refs.add(f"#/types/{name}")
            for method in type_def.get("methods", []):
                mname = method.get("name")
                if mname:
                    refs.add(f"#/types/{name}/methods/{mname}")

    # Functions
    for func in library.get("functions", []):
        name = func.get("name")
        if name:
            refs.add(f"#/functions/{name}")

    # Features
    for feature in library.get("features", []):
        fid = feature.get("id")
        if fid:
            refs.add(f"#/features/{fid}")

    # Modules
    for module in library.get("modules", []):
        path = module.get("path")
        if path:
            refs.add(f"#/modules/{path}")

    # Principles
    for principle in library.get("principles", []):
        pid = principle.get("id")
        if pid:
            refs.add(f"#/principles/{pid}")

    return refs


@RuleRegistry.register
class DanglingReference(LintRule):
    """Cross-references should point to existing entities."""

    id = "X001"
    name = "dangling-reference"
    description = "Reference points to non-existent entity"
    default_severity = Severity.ERROR
    category = "consistency"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        valid_refs = collect_valid_refs(spec)
        library = spec.get("library", {})
        severity = self.get_severity(config)

        # Check feature references
        for i, feature in enumerate(library.get("features", [])):
            for ref in feature.get("references", []):
                # Skip external references (contain library prefix)
                if "#" in ref and not ref.startswith("#"):
                    continue
                if ref not in valid_refs:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Reference '{ref}' does not exist",
                        path=f"$.library.features[{i}].references",
                        ref=f"#/features/{feature.get('id')}",
                    )

        # Check type references (bases, related)
        for i, type_def in enumerate(library.get("types", [])):
            for ref in type_def.get("related", []):
                if ref.startswith("#") and ref not in valid_refs:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Related reference '{ref}' does not exist",
                        path=f"$.library.types[{i}].related",
                        ref=f"#/types/{type_def.get('name')}",
                    )


@RuleRegistry.register
class DuplicateTypeName(LintRule):
    """Type names must be unique."""

    id = "X002"
    name = "duplicate-type-name"
    description = "Multiple types with same name"
    default_severity = Severity.ERROR
    category = "consistency"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        seen: dict[str, int] = {}
        for i, type_def in enumerate(types):
            name = type_def.get("name")
            if name:
                if name in seen:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Duplicate type name '{name}' (also at index {seen[name]})",
                        path=f"$.library.types[{i}]",
                        ref=f"#/types/{name}",
                    )
                else:
                    seen[name] = i


@RuleRegistry.register
class DuplicateFeatureId(LintRule):
    """Feature IDs must be unique."""

    id = "X003"
    name = "duplicate-feature-id"
    description = "Multiple features with same ID"
    default_severity = Severity.ERROR
    category = "consistency"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        seen: dict[str, int] = {}
        for i, feature in enumerate(features):
            fid = feature.get("id")
            if fid:
                if fid in seen:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Duplicate feature ID '{fid}' (also at index {seen[fid]})",
                        path=f"$.library.features[{i}]",
                        ref=f"#/features/{fid}",
                    )
                else:
                    seen[fid] = i


@RuleRegistry.register
class InvalidStatusTransition(LintRule):
    """Feature status should be logically consistent."""

    id = "X006"
    name = "invalid-status-transition"
    description = "Feature status inconsistent (tested but not implemented)"
    default_severity = Severity.WARNING
    category = "consistency"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            status = feature.get("status", "planned")
            steps = feature.get("steps", [])

            # "tested" should imply the feature is implemented
            # We can't actually verify this programmatically, but we can
            # warn if status is "tested" but there are no steps
            if status == "tested" and not steps:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature '{feature.get('id', '?')}' marked as tested but has no verification steps",
                    path=f"$.library.features[{i}]",
                    ref=f"#/features/{feature.get('id')}",
                )
