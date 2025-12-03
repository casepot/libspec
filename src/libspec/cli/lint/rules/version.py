"""Python version lint rules (V001-V099).

These rules check for version-specific typing features and ensure
that python_added fields are consistent with python_requires.
"""

from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry
from libspec.python_versions import (
    DEPRECATED_PATTERNS,
    TYPING_EXTENSIONS_BACKPORTS,
    detect_type_features,
    is_version_compatible,
    parse_python_requires,
    version_compare,
)


def _check_python_added(
    entity_path: str,
    entity_ref: str,
    python_added: str | None,
    library_requires: str | None,
    severity: Severity,
) -> Iterator[LintIssue]:
    """Check if python_added is compatible with library's python_requires."""
    if python_added is None or library_requires is None:
        return

    if not is_version_compatible(python_added, library_requires):
        min_version = parse_python_requires(library_requires)
        yield LintIssue(
            rule="V001",
            severity=severity,
            message=(
                f"python_added '{python_added}' is newer than library's "
                f"python_requires '{library_requires}' (min: {min_version})"
            ),
            path=entity_path,
            ref=entity_ref,
        )


def _check_callable_nested_fields(
    callable_obj: dict[str, Any],
    base_path: str,
    base_ref: str,
    library_requires: str | None,
    severity: Severity,
) -> Iterator[LintIssue]:
    """Check nested python_added fields in a callable (method/function).

    Checks: returns, parameters, raises, overloads, yields, async_yields.
    """
    # Check returns
    returns = callable_obj.get("returns")
    if returns and isinstance(returns, dict):
        yield from _check_python_added(
            f"{base_path}.returns.python_added",
            f"{base_ref}/returns",
            returns.get("python_added"),
            library_requires,
            severity,
        )

    # Check parameters
    for k, param in enumerate(callable_obj.get("parameters", [])):
        param_name = param.get("name", "")
        yield from _check_python_added(
            f"{base_path}.parameters[{k}].python_added",
            f"{base_ref}/parameters/{param_name}",
            param.get("python_added"),
            library_requires,
            severity,
        )

    # Check raises
    for k, raises in enumerate(callable_obj.get("raises", [])):
        yield from _check_python_added(
            f"{base_path}.raises[{k}].python_added",
            f"{base_ref}/raises/{k}",
            raises.get("python_added"),
            library_requires,
            severity,
        )

    # Check overloads
    for k, overload in enumerate(callable_obj.get("overloads", [])):
        yield from _check_python_added(
            f"{base_path}.overloads[{k}].python_added",
            f"{base_ref}/overloads/{k}",
            overload.get("python_added"),
            library_requires,
            severity,
        )

    # Check yields (for generators)
    yields = callable_obj.get("yields")
    if yields and isinstance(yields, dict):
        yield from _check_python_added(
            f"{base_path}.yields.python_added",
            f"{base_ref}/yields",
            yields.get("python_added"),
            library_requires,
            severity,
        )

    # Check async_yields (for async generators)
    async_yields = callable_obj.get("async_yields")
    if async_yields and isinstance(async_yields, dict):
        yield from _check_python_added(
            f"{base_path}.async_yields.python_added",
            f"{base_ref}/async_yields",
            async_yields.get("python_added"),
            library_requires,
            severity,
        )


def _check_signature_features(
    entity_path: str,
    entity_ref: str,
    signature: str,
    library_requires: str | None,
    severity: Severity,
) -> Iterator[LintIssue]:
    """Check if signature uses version-specific features."""
    if library_requires is None:
        return

    min_version = parse_python_requires(library_requires)
    if min_version is None:
        return

    features = list(detect_type_features(signature))
    for feature_name, feature_version, _context in features:
        if version_compare(feature_version, min_version) > 0:
            yield LintIssue(
                rule="V002",
                severity=severity,
                message=(
                    f"Signature uses '{feature_name}' (Python {feature_version}+) but "
                    f"library requires Python {min_version}+"
                ),
                path=entity_path,
                ref=entity_ref,
            )


@RuleRegistry.register
class PythonAddedCompatibility(LintRule):
    """Check that python_added fields are compatible with python_requires."""

    id = "V001"
    name = "python-added-compat"
    description = "Feature's python_added should not exceed library's python_requires"
    default_severity = Severity.WARNING
    category = "version"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        # Check types
        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name", "")
            python_added = type_def.get("python_added")
            yield from _check_python_added(
                f"$.library.types[{i}].python_added",
                f"#/types/{name}",
                python_added,
                python_requires,
                severity,
            )

            # Check methods (and nested fields)
            for j, method in enumerate(type_def.get("methods", [])):
                method_name = method.get("name", "")
                method_added = method.get("python_added")
                base_path = f"$.library.types[{i}].methods[{j}]"
                base_ref = f"#/types/{name}/methods/{method_name}"
                yield from _check_python_added(
                    f"{base_path}.python_added",
                    base_ref,
                    method_added,
                    python_requires,
                    severity,
                )
                # Check nested fields (returns, parameters, raises, overloads, yields)
                yield from _check_callable_nested_fields(
                    method, base_path, base_ref, python_requires, severity
                )

            # Check class_methods (and nested fields)
            for j, method in enumerate(type_def.get("class_methods", [])):
                method_name = method.get("name", "")
                method_added = method.get("python_added")
                base_path = f"$.library.types[{i}].class_methods[{j}]"
                base_ref = f"#/types/{name}/class_methods/{method_name}"
                yield from _check_python_added(
                    f"{base_path}.python_added",
                    base_ref,
                    method_added,
                    python_requires,
                    severity,
                )
                yield from _check_callable_nested_fields(
                    method, base_path, base_ref, python_requires, severity
                )

            # Check static_methods (and nested fields)
            for j, method in enumerate(type_def.get("static_methods", [])):
                method_name = method.get("name", "")
                method_added = method.get("python_added")
                base_path = f"$.library.types[{i}].static_methods[{j}]"
                base_ref = f"#/types/{name}/static_methods/{method_name}"
                yield from _check_python_added(
                    f"{base_path}.python_added",
                    base_ref,
                    method_added,
                    python_requires,
                    severity,
                )
                yield from _check_callable_nested_fields(
                    method, base_path, base_ref, python_requires, severity
                )

            # Check construction (and nested fields)
            construction = type_def.get("construction")
            if construction:
                base_path = f"$.library.types[{i}].construction"
                base_ref = f"#/types/{name}/construction"
                yield from _check_python_added(
                    f"{base_path}.python_added",
                    base_ref,
                    construction.get("python_added"),
                    python_requires,
                    severity,
                )
                # Check construction parameters
                for k, param in enumerate(construction.get("parameters", [])):
                    param_name = param.get("name", "")
                    yield from _check_python_added(
                        f"{base_path}.parameters[{k}].python_added",
                        f"{base_ref}/parameters/{param_name}",
                        param.get("python_added"),
                        python_requires,
                        severity,
                    )
                # Check construction raises
                for k, raises in enumerate(construction.get("raises", [])):
                    yield from _check_python_added(
                        f"{base_path}.raises[{k}].python_added",
                        f"{base_ref}/raises/{k}",
                        raises.get("python_added"),
                        python_requires,
                        severity,
                    )

            # Check properties
            for j, prop in enumerate(type_def.get("properties", [])):
                prop_name = prop.get("name", "")
                prop_added = prop.get("python_added")
                yield from _check_python_added(
                    f"$.library.types[{i}].properties[{j}].python_added",
                    f"#/types/{name}/properties/{prop_name}",
                    prop_added,
                    python_requires,
                    severity,
                )

            # Check generic params
            for j, gparam in enumerate(type_def.get("generic_params", [])):
                gparam_name = gparam.get("name", "")
                gparam_added = gparam.get("python_added")
                yield from _check_python_added(
                    f"$.library.types[{i}].generic_params[{j}].python_added",
                    f"#/types/{name}/generic_params/{gparam_name}",
                    gparam_added,
                    python_requires,
                    severity,
                )

        # Check functions (and nested fields)
        for i, func in enumerate(library.get("functions", [])):
            name = func.get("name", "")
            python_added = func.get("python_added")
            base_path = f"$.library.functions[{i}]"
            base_ref = f"#/functions/{name}"
            yield from _check_python_added(
                f"{base_path}.python_added",
                base_ref,
                python_added,
                python_requires,
                severity,
            )
            # Check nested fields (returns, parameters, raises, overloads, yields)
            yield from _check_callable_nested_fields(
                func, base_path, base_ref, python_requires, severity
            )


@RuleRegistry.register
class SignatureVersionFeatures(LintRule):
    """Check that signatures don't use features newer than python_requires."""

    id = "V002"
    name = "signature-version-features"
    description = "Signature uses typing features newer than python_requires"
    default_severity = Severity.WARNING
    category = "version"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is None:
            return  # Can't check without python_requires

        # Check types
        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name", "")

            # Check methods
            for j, method in enumerate(type_def.get("methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    yield from _check_signature_features(
                        f"$.library.types[{i}].methods[{j}].signature",
                        f"#/types/{name}/methods/{method_name}",
                        signature,
                        python_requires,
                        severity,
                    )

            # Check class methods
            for j, method in enumerate(type_def.get("class_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    yield from _check_signature_features(
                        f"$.library.types[{i}].class_methods[{j}].signature",
                        f"#/types/{name}/class_methods/{method_name}",
                        signature,
                        python_requires,
                        severity,
                    )

            # Check static methods
            for j, method in enumerate(type_def.get("static_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    yield from _check_signature_features(
                        f"$.library.types[{i}].static_methods[{j}].signature",
                        f"#/types/{name}/static_methods/{method_name}",
                        signature,
                        python_requires,
                        severity,
                    )

        # Check functions
        for i, func in enumerate(library.get("functions", [])):
            name = func.get("name", "")
            signature = func.get("signature", "")
            if signature:
                yield from _check_signature_features(
                    f"$.library.functions[{i}].signature",
                    f"#/functions/{name}",
                    signature,
                    python_requires,
                    severity,
                )


@RuleRegistry.register
class MissingPythonRequires(LintRule):
    """Check that libraries using version-specific features declare python_requires."""

    id = "V003"
    name = "missing-python-requires"
    description = "Library uses version-specific features but missing python_requires"
    default_severity = Severity.INFO
    category = "version"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is not None:
            return  # Already has python_requires

        # Collect all signatures and check for version-specific features
        all_features: list[tuple[str, str, str]] = []

        for type_def in library.get("types", []):
            for method in type_def.get("methods", []):
                signature = method.get("signature", "")
                if signature:
                    all_features.extend(detect_type_features(signature))

            for method in type_def.get("class_methods", []):
                signature = method.get("signature", "")
                if signature:
                    all_features.extend(detect_type_features(signature))

            for method in type_def.get("static_methods", []):
                signature = method.get("signature", "")
                if signature:
                    all_features.extend(detect_type_features(signature))

        for func in library.get("functions", []):
            signature = func.get("signature", "")
            if signature:
                all_features.extend(detect_type_features(signature))

        # Get configurable baseline (defaults to 3.8)
        baseline = config.get("lint", {}).get("baseline_python_version", "3.8")
        # Compare version strings - features newer than baseline trigger this rule
        notable_features = [
            f for f in all_features if version_compare(f[1], baseline) > 0
        ]
        if notable_features:
            # Find the highest required version
            highest_version = max(f[1] for f in notable_features)
            feature_examples = ", ".join(
                sorted({f[0] for f in notable_features if f[1] == highest_version})[:3]
            )
            yield LintIssue(
                rule="V003",
                severity=severity,
                message=(
                    f"Library uses Python {highest_version}+ features ({feature_examples}) "
                    "but does not declare python_requires"
                ),
                path="$.library.python_requires",
                ref="#/library",
            )


@RuleRegistry.register
class GenericParamVersionFeatures(LintRule):
    """Check that generic parameter kinds and features match declared versions."""

    id = "V004"
    name = "generic-param-version"
    description = "Generic parameter uses version-specific construct"
    default_severity = Severity.WARNING
    category = "version"

    # Mapping of generic param kinds to their required Python versions
    KIND_VERSIONS = {
        "type_var": "3.8",
        "param_spec": "3.10",
        "type_var_tuple": "3.11",
    }

    # PEP 696 - TypeVar defaults require Python 3.13
    DEFAULT_VERSION = "3.13"

    def _check_gparam(
        self,
        gparam: dict[str, Any],
        gparam_idx: int,
        entity_name: str,
        entity_type: str,
        entity_idx: int,
        min_version: str,
        severity: Severity,
    ) -> Iterator[LintIssue]:
        """Check a single generic parameter for version issues."""
        gparam_name = gparam.get("name", "")
        kind = gparam.get("kind", "type_var")
        required_version = self.KIND_VERSIONS.get(kind, "3.8")

        # Check kind version
        if version_compare(required_version, min_version) > 0:
            yield LintIssue(
                rule="V004",
                severity=severity,
                message=(
                    f"Generic parameter '{gparam_name}' uses {kind} "
                    f"(Python {required_version}+) but library requires "
                    f"Python {min_version}+"
                ),
                path=f"$.library.{entity_type}[{entity_idx}].generic_params[{gparam_idx}].kind",
                ref=f"#/{entity_type}/{entity_name}/generic_params/{gparam_name}",
            )

        # Check default field (PEP 696, Python 3.13+)
        if gparam.get("default") is not None:
            if version_compare(self.DEFAULT_VERSION, min_version) > 0:
                yield LintIssue(
                    rule="V004",
                    severity=severity,
                    message=(
                        f"Generic parameter '{gparam_name}' uses default value "
                        f"(PEP 696, Python {self.DEFAULT_VERSION}+) but library requires "
                        f"Python {min_version}+"
                    ),
                    path=f"$.library.{entity_type}[{entity_idx}].generic_params[{gparam_idx}].default",
                    ref=f"#/{entity_type}/{entity_name}/generic_params/{gparam_name}",
                )

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is None:
            return

        min_version = parse_python_requires(python_requires)
        if min_version is None:
            return

        # Check types
        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name", "")

            for j, gparam in enumerate(type_def.get("generic_params", [])):
                yield from self._check_gparam(
                    gparam, j, name, "types", i, min_version, severity
                )

        # Check functions
        for i, func in enumerate(library.get("functions", [])):
            name = func.get("name", "")

            for j, gparam in enumerate(func.get("generic_params", [])):
                yield from self._check_gparam(
                    gparam, j, name, "functions", i, min_version, severity
                )


@RuleRegistry.register
class ExceptionGroupVersionFeatures(LintRule):
    """Check that exception group features match python_requires."""

    id = "V005"
    name = "exception-group-version"
    description = "Exception groups require Python 3.11+"
    default_severity = Severity.WARNING
    category = "version"

    # Exception group types (PEP 654, Python 3.11)
    EXCEPTION_GROUP_TYPES = {"BaseExceptionGroup", "ExceptionGroup"}
    REQUIRED_VERSION = "3.11"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is None:
            return

        min_version = parse_python_requires(python_requires)
        if min_version is None:
            return

        # Only check if library requires < 3.11
        if version_compare(self.REQUIRED_VERSION, min_version) <= 0:
            return

        # Check types for raises clauses
        for i, type_def in enumerate(library.get("types", [])):
            type_name = type_def.get("name", "")

            # Check methods
            for j, method in enumerate(type_def.get("methods", [])):
                method_name = method.get("name", "")
                for k, raises in enumerate(method.get("raises", [])):
                    exc_type = raises.get("type", "")
                    if exc_type in self.EXCEPTION_GROUP_TYPES:
                        yield LintIssue(
                            rule="V005",
                            severity=severity,
                            message=(
                                f"Method '{method_name}' raises {exc_type} "
                                f"(Python {self.REQUIRED_VERSION}+) but library requires "
                                f"Python {min_version}+"
                            ),
                            path=f"$.library.types[{i}].methods[{j}].raises[{k}].type",
                            ref=f"#/types/{type_name}/methods/{method_name}",
                        )

            # Check class methods
            for j, method in enumerate(type_def.get("class_methods", [])):
                method_name = method.get("name", "")
                for k, raises in enumerate(method.get("raises", [])):
                    exc_type = raises.get("type", "")
                    if exc_type in self.EXCEPTION_GROUP_TYPES:
                        yield LintIssue(
                            rule="V005",
                            severity=severity,
                            message=(
                                f"Class method '{method_name}' raises {exc_type} "
                                f"(Python {self.REQUIRED_VERSION}+) but library requires "
                                f"Python {min_version}+"
                            ),
                            path=f"$.library.types[{i}].class_methods[{j}].raises[{k}].type",
                            ref=f"#/types/{type_name}/class_methods/{method_name}",
                        )

            # Check constructor
            constructor = type_def.get("construction")
            if constructor:
                for k, raises in enumerate(constructor.get("raises", [])):
                    exc_type = raises.get("type", "")
                    if exc_type in self.EXCEPTION_GROUP_TYPES:
                        yield LintIssue(
                            rule="V005",
                            severity=severity,
                            message=(
                                f"Constructor of '{type_name}' raises {exc_type} "
                                f"(Python {self.REQUIRED_VERSION}+) but library requires "
                                f"Python {min_version}+"
                            ),
                            path=f"$.library.types[{i}].construction.raises[{k}].type",
                            ref=f"#/types/{type_name}/construction",
                        )

        # Check functions
        for i, func in enumerate(library.get("functions", [])):
            func_name = func.get("name", "")
            for k, raises in enumerate(func.get("raises", [])):
                exc_type = raises.get("type", "")
                if exc_type in self.EXCEPTION_GROUP_TYPES:
                    yield LintIssue(
                        rule="V005",
                        severity=severity,
                        message=(
                            f"Function '{func_name}' raises {exc_type} "
                            f"(Python {self.REQUIRED_VERSION}+) but library requires "
                            f"Python {min_version}+"
                        ),
                        path=f"$.library.functions[{i}].raises[{k}].type",
                        ref=f"#/functions/{func_name}",
                    )


def _check_typing_extensions_needed(
    signature: str,
    min_version: str,
) -> Iterator[tuple[str, str, str]]:
    """Check if signature uses features that need typing_extensions.

    Yields:
        Tuples of (feature_name, stdlib_version, typing_extensions_version).
    """
    import re

    for feature, (stdlib_ver, te_ver) in TYPING_EXTENSIONS_BACKPORTS.items():
        # Use word boundary to avoid partial matches
        pattern = rf"\b{re.escape(feature)}\b"
        if re.search(pattern, signature):
            # Only report if stdlib version is newer than target
            if version_compare(stdlib_ver, min_version) > 0:
                yield (feature, stdlib_ver, te_ver)


def _check_deprecated_patterns(
    signature: str,
    min_version: str,
) -> Iterator[tuple[str, str, str, str]]:
    """Check if signature uses deprecated typing patterns.

    Yields:
        Tuples of (old_style, new_style, deprecated_since, found_pattern).
    """
    import re

    for pattern, old_style, new_style, deprecated_since in DEPRECATED_PATTERNS:
        # Only suggest if target version supports the new syntax
        if version_compare(min_version, deprecated_since) >= 0:
            if re.search(pattern, signature):
                yield (old_style, new_style, deprecated_since, pattern)


@RuleRegistry.register
class TypingExtensionsBackport(LintRule):
    """Detect features that require typing_extensions for older Python versions."""

    id = "V006"
    name = "typing-extensions-backport"
    description = "Feature requires typing_extensions for older Python versions"
    default_severity = Severity.INFO
    category = "version"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is None:
            return

        min_version = parse_python_requires(python_requires)
        if min_version is None:
            return

        # Collect all signatures
        signatures_to_check: list[tuple[str, str, str]] = []  # (sig, path, ref)

        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name", "")

            for j, method in enumerate(type_def.get("methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].methods[{j}].signature",
                        f"#/types/{name}/methods/{method_name}",
                    ))

            for j, method in enumerate(type_def.get("class_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].class_methods[{j}].signature",
                        f"#/types/{name}/class_methods/{method_name}",
                    ))

            for j, method in enumerate(type_def.get("static_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].static_methods[{j}].signature",
                        f"#/types/{name}/static_methods/{method_name}",
                    ))

        for i, func in enumerate(library.get("functions", [])):
            name = func.get("name", "")
            signature = func.get("signature", "")
            if signature:
                signatures_to_check.append((
                    signature,
                    f"$.library.functions[{i}].signature",
                    f"#/functions/{name}",
                ))

        # Check each signature
        for signature, path, ref in signatures_to_check:
            for feature, stdlib_ver, te_ver in _check_typing_extensions_needed(
                signature, min_version
            ):
                yield LintIssue(
                    rule="V006",
                    severity=severity,
                    message=(
                        f"'{feature}' requires Python {stdlib_ver}+ or "
                        f"typing_extensions>={te_ver} for Python {min_version}"
                    ),
                    path=path,
                    ref=ref,
                    suggested_fix=f"from typing_extensions import {feature}",
                )


@RuleRegistry.register
class DeprecatedTypingPatterns(LintRule):
    """Detect deprecated typing patterns that can be modernized."""

    id = "V007"
    name = "deprecated-typing-patterns"
    description = "Signature uses deprecated typing patterns"
    default_severity = Severity.INFO
    category = "version"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        library = spec.get("library", {})
        python_requires = library.get("python_requires")
        severity = self.get_severity(config)

        if python_requires is None:
            return

        min_version = parse_python_requires(python_requires)
        if min_version is None:
            return

        # Collect all signatures
        signatures_to_check: list[tuple[str, str, str]] = []  # (sig, path, ref)

        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name", "")

            for j, method in enumerate(type_def.get("methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].methods[{j}].signature",
                        f"#/types/{name}/methods/{method_name}",
                    ))

            for j, method in enumerate(type_def.get("class_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].class_methods[{j}].signature",
                        f"#/types/{name}/class_methods/{method_name}",
                    ))

            for j, method in enumerate(type_def.get("static_methods", [])):
                method_name = method.get("name", "")
                signature = method.get("signature", "")
                if signature:
                    signatures_to_check.append((
                        signature,
                        f"$.library.types[{i}].static_methods[{j}].signature",
                        f"#/types/{name}/static_methods/{method_name}",
                    ))

        for i, func in enumerate(library.get("functions", [])):
            name = func.get("name", "")
            signature = func.get("signature", "")
            if signature:
                signatures_to_check.append((
                    signature,
                    f"$.library.functions[{i}].signature",
                    f"#/functions/{name}",
                ))

        # Check each signature
        for signature, path, ref in signatures_to_check:
            for old_style, new_style, deprecated_since, _ in _check_deprecated_patterns(
                signature, min_version
            ):
                yield LintIssue(
                    rule="V007",
                    severity=severity,
                    message=(
                        f"'{old_style}' is deprecated since Python {deprecated_since}, "
                        f"use '{new_style}' instead"
                    ),
                    path=path,
                    ref=ref,
                    suggested_fix=f"Replace {old_style} with {new_style}",
                )
