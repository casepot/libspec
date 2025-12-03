"""Structural lint rules (S001-S099)."""

from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


@RuleRegistry.register
class MissingTypeDescription(LintRule):
    """Type definitions should have a docstring."""

    id = "S001"
    name = "missing-type-description"
    description = "Type definitions should have a docstring"
    default_severity = Severity.ERROR
    category = "structural"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            if not type_def.get("docstring"):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Type '{type_def.get('name', 'unknown')}' missing docstring",
                    path=f"$.library.types[{i}]",
                    ref=f"#/types/{type_def.get('name')}",
                )


@RuleRegistry.register
class MissingMethodDescription(LintRule):
    """Methods should have a description."""

    id = "S002"
    name = "missing-method-description"
    description = "Methods should have a description"
    default_severity = Severity.WARNING
    category = "structural"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            type_name = type_def.get("name", "unknown")
            for j, method in enumerate(type_def.get("methods", [])):
                if not method.get("description"):
                    mname = method.get("name", "?")
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Method '{type_name}.{mname}' missing description",
                        path=f"$.library.types[{i}].methods[{j}]",
                        ref=f"#/types/{type_name}/methods/{mname}",
                    )


@RuleRegistry.register
class MissingFunctionDescription(LintRule):
    """Functions should have a description."""

    id = "S003"
    name = "missing-function-description"
    description = "Functions should have a description"
    default_severity = Severity.WARNING
    category = "structural"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        functions = spec.get("library", {}).get("functions", [])
        severity = self.get_severity(config)

        for i, func in enumerate(functions):
            if not func.get("description"):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Function '{func.get('name', '?')}' missing description",
                    path=f"$.library.functions[{i}]",
                    ref=f"#/functions/{func.get('name')}",
                )


@RuleRegistry.register
class EmptyType(LintRule):
    """Types should have methods or properties."""

    id = "S007"
    name = "empty-type"
    description = "Type has no methods or properties"
    default_severity = Severity.WARNING
    category = "structural"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            # Enums and type aliases are allowed to be "empty" of methods
            kind = type_def.get("kind", "class")
            if kind in ("enum", "type_alias"):
                continue

            methods = type_def.get("methods", [])
            properties = type_def.get("properties", [])
            class_methods = type_def.get("class_methods", [])
            static_methods = type_def.get("static_methods", [])

            total = len(methods) + len(properties) + len(class_methods) + len(static_methods)
            if total == 0:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Type '{type_def.get('name', '?')}' has no methods or properties",
                    path=f"$.library.types[{i}]",
                    ref=f"#/types/{type_def.get('name')}",
                )
