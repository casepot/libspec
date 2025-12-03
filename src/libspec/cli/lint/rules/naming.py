"""Naming lint rules (N001-N099)."""

import re
from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


def is_kebab_case(s: str) -> bool:
    """Check if string is kebab-case."""
    return bool(re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", s))


def is_screaming_snake_case(s: str) -> bool:
    """Check if string is SCREAMING_SNAKE_CASE."""
    return bool(re.match(r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$", s))


def is_pascal_case(s: str) -> bool:
    """Check if string is PascalCase."""
    return bool(re.match(r"^[A-Z][a-zA-Z0-9]*$", s))


def is_snake_case(s: str) -> bool:
    """Check if string is snake_case."""
    return bool(re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", s))


def to_kebab_case(s: str) -> str:
    """Convert to kebab-case."""
    # Handle camelCase and PascalCase
    s = re.sub(r"([a-z])([A-Z])", r"\1-\2", s)
    # Handle underscores
    s = s.replace("_", "-")
    return s.lower()


@RuleRegistry.register
class FeatureIdFormat(LintRule):
    """Feature IDs should be kebab-case."""

    id = "N001"
    name = "feature-id-format"
    description = "Feature ID should be kebab-case"
    default_severity = Severity.WARNING
    category = "naming"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            fid = feature.get("id", "")
            if fid and not is_kebab_case(fid):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature ID '{fid}' should be kebab-case",
                    path=f"$.library.features[{i}].id",
                    ref=f"#/features/{fid}",
                    fix_available=True,
                    suggested_fix=to_kebab_case(fid),
                )


@RuleRegistry.register
class PrincipleIdFormat(LintRule):
    """Principle IDs should be kebab-case."""

    id = "N002"
    name = "principle-id-format"
    description = "Principle ID should be kebab-case"
    default_severity = Severity.WARNING
    category = "naming"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        principles = spec.get("library", {}).get("principles", [])
        severity = self.get_severity(config)

        for i, principle in enumerate(principles):
            pid = principle.get("id", "")
            if pid and not is_kebab_case(pid):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Principle ID '{pid}' should be kebab-case",
                    path=f"$.library.principles[{i}].id",
                    fix_available=True,
                    suggested_fix=to_kebab_case(pid),
                )


@RuleRegistry.register
class TypeNamePascal(LintRule):
    """Type names should be PascalCase."""

    id = "N003"
    name = "type-name-pascal"
    description = "Type names should be PascalCase"
    default_severity = Severity.WARNING
    category = "naming"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            name = type_def.get("name", "")
            if name and not is_pascal_case(name):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Type name '{name}' should be PascalCase",
                    path=f"$.library.types[{i}].name",
                    ref=f"#/types/{name}",
                )


@RuleRegistry.register
class FunctionNameSnake(LintRule):
    """Function names should be snake_case."""

    id = "N004"
    name = "function-name-snake"
    description = "Function names should be snake_case"
    default_severity = Severity.WARNING
    category = "naming"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        functions = spec.get("library", {}).get("functions", [])
        severity = self.get_severity(config)

        for i, func in enumerate(functions):
            name = func.get("name", "")
            # Allow dunder methods like __init__
            if name and not name.startswith("__") and not is_snake_case(name):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Function name '{name}' should be snake_case",
                    path=f"$.library.functions[{i}].name",
                    ref=f"#/functions/{name}",
                )


@RuleRegistry.register
class CategoryScreamingSnake(LintRule):
    """Feature category should be SCREAMING_SNAKE_CASE."""

    id = "N006"
    name = "category-screaming-snake"
    description = "Feature category should be SCREAMING_SNAKE_CASE"
    default_severity = Severity.WARNING
    category = "naming"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            cat = feature.get("category", "")
            if cat and not is_screaming_snake_case(cat):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature category '{cat}' should be SCREAMING_SNAKE_CASE",
                    path=f"$.library.features[{i}].category",
                    ref=f"#/features/{feature.get('id')}",
                )
