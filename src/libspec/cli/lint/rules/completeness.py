"""Completeness lint rules (C001-C099)."""

from typing import Any, Iterator

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


@RuleRegistry.register
class FeatureNoSteps(LintRule):
    """Features should have verification steps."""

    id = "C001"
    name = "feature-no-steps"
    description = "Feature has no verification steps"
    default_severity = Severity.WARNING
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            steps = feature.get("steps", [])
            if not steps:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature '{feature.get('id', '?')}' has no verification steps",
                    path=f"$.library.features[{i}]",
                    ref=f"#/features/{feature.get('id')}",
                )


@RuleRegistry.register
class MethodNoSignature(LintRule):
    """Methods must have a signature."""

    id = "C002"
    name = "method-no-signature"
    description = "Method missing signature"
    default_severity = Severity.ERROR
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            type_name = type_def.get("name", "unknown")
            for j, method in enumerate(type_def.get("methods", [])):
                if not method.get("signature"):
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Method '{type_name}.{method.get('name', '?')}' missing signature",
                        path=f"$.library.types[{i}].methods[{j}]",
                        ref=f"#/types/{type_name}/methods/{method.get('name')}",
                    )


@RuleRegistry.register
class TypeNoModule(LintRule):
    """Types must have a module path."""

    id = "C003"
    name = "type-no-module"
    description = "Type missing module path"
    default_severity = Severity.ERROR
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            if not type_def.get("module"):
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Type '{type_def.get('name', '?')}' missing module path",
                    path=f"$.library.types[{i}]",
                    ref=f"#/types/{type_def.get('name')}",
                )


@RuleRegistry.register
class EnumNoValues(LintRule):
    """Enum types should have values defined."""

    id = "C005"
    name = "enum-no-values"
    description = "Enum type has no values defined"
    default_severity = Severity.WARNING
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            if type_def.get("kind") == "enum":
                values = type_def.get("values", [])
                if not values:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Enum '{type_def.get('name', '?')}' has no values defined",
                        path=f"$.library.types[{i}]",
                        ref=f"#/types/{type_def.get('name')}",
                    )


@RuleRegistry.register
class ProtocolNoMethods(LintRule):
    """Protocol types should have abstract methods."""

    id = "C006"
    name = "protocol-no-methods"
    description = "Protocol with no abstract methods"
    default_severity = Severity.WARNING
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            if type_def.get("kind") == "protocol":
                methods = type_def.get("methods", [])
                properties = type_def.get("properties", [])
                if not methods and not properties:
                    name = type_def.get("name", "?")
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Protocol '{name}' has no methods or properties",
                        path=f"$.library.types[{i}]",
                        ref=f"#/types/{name}",
                    )


@RuleRegistry.register
class FeatureNoReferences(LintRule):
    """Features should have cross-references."""

    id = "C007"
    name = "feature-no-references"
    description = "Feature has no cross-references"
    default_severity = Severity.INFO
    category = "completeness"

    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            refs = feature.get("references", [])
            if not refs:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature '{feature.get('id', '?')}' has no cross-references",
                    path=f"$.library.features[{i}]",
                    ref=f"#/features/{feature.get('id')}",
                )
