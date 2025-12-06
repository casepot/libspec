"""Consistency lint rules (X001-X099)."""

from typing import Any, Iterator

from typing_extensions import override

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

    @override
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

            # Check requires refs on features
            for j, req in enumerate(feature.get("requires", [])):
                ref = req.get("ref") if isinstance(req, dict) else None
                if ref and ref.startswith("#") and ref not in valid_refs:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Requirement reference '{ref}' does not exist",
                        path=f"$.library.features[{i}].requires[{j}].ref",
                        ref=f"#/features/{feature.get('id')}",
                    )

        # Check type references (bases, related, requires)
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

            # Check requires refs on types
            for j, req in enumerate(type_def.get("requires", [])):
                ref = req.get("ref") if isinstance(req, dict) else None
                if ref and ref.startswith("#") and ref not in valid_refs:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Requirement reference '{ref}' does not exist",
                        path=f"$.library.types[{i}].requires[{j}].ref",
                        ref=f"#/types/{type_def.get('name')}",
                    )

        # Check function requires refs
        for i, func in enumerate(library.get("functions", [])):
            for j, req in enumerate(func.get("requires", [])):
                ref = req.get("ref") if isinstance(req, dict) else None
                if ref and ref.startswith("#") and ref not in valid_refs:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Requirement reference '{ref}' does not exist",
                        path=f"$.library.functions[{i}].requires[{j}].ref",
                        ref=f"#/functions/{func.get('name')}",
                    )


@RuleRegistry.register
class DuplicateTypeName(LintRule):
    """Type names must be unique."""

    id = "X002"
    name = "duplicate-type-name"
    description = "Multiple types with same name"
    default_severity = Severity.ERROR
    category = "consistency"

    @override
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

    @override
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

    @override
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
                fid = feature.get("id", "?")
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Feature '{fid}' marked tested but has no steps",
                    path=f"$.library.features[{i}]",
                    ref=f"#/features/{fid}",
                )


def build_requirement_graph(spec: dict[str, Any]) -> dict[str, list[str]]:
    """Build a dependency graph from all requires fields.

    Returns:
        Dict mapping entity refs to their required entity refs.
    """
    graph: dict[str, list[str]] = {}
    library = spec.get("library", {})

    # Types
    for type_def in library.get("types", []):
        name = type_def.get("name")
        if name:
            ref = f"#/types/{name}"
            deps = []
            for req in type_def.get("requires", []):
                if isinstance(req, dict) and req.get("ref"):
                    deps.append(req["ref"])
            if deps:
                graph[ref] = deps

    # Functions
    for func in library.get("functions", []):
        name = func.get("name")
        if name:
            ref = f"#/functions/{name}"
            deps = []
            for req in func.get("requires", []):
                if isinstance(req, dict) and req.get("ref"):
                    deps.append(req["ref"])
            if deps:
                graph[ref] = deps

    # Features
    for feature in library.get("features", []):
        fid = feature.get("id")
        if fid:
            ref = f"#/features/{fid}"
            deps = []
            for req in feature.get("requires", []):
                if isinstance(req, dict) and req.get("ref"):
                    deps.append(req["ref"])
            if deps:
                graph[ref] = deps

    return graph


def find_cycle(graph: dict[str, list[str]]) -> list[str] | None:
    """Find a cycle in the dependency graph using DFS.

    Returns:
        List of refs forming the cycle, or None if no cycle.
    """
    visited: set[str] = set()
    rec_stack: set[str] = set()
    path: list[str] = []

    def dfs(node: str) -> list[str] | None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                result = dfs(neighbor)
                if result:
                    return result
            elif neighbor in rec_stack:
                # Found cycle - extract the cycle portion
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]

        path.pop()
        rec_stack.remove(node)
        return None

    for node in graph:
        if node not in visited:
            result = dfs(node)
            if result:
                return result

    return None


@RuleRegistry.register
class CircularRequirement(LintRule):
    """Circular dependencies in requires chains are not allowed."""

    id = "X004"
    name = "circular-requirement"
    description = "Circular dependency detected in requires chain"
    default_severity = Severity.ERROR
    category = "consistency"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        severity = self.get_severity(config)
        graph = build_requirement_graph(spec)
        cycle = find_cycle(graph)

        if cycle:
            cycle_str = " -> ".join(cycle)
            # Get the first entity in the cycle for the issue location
            first_ref = cycle[0]
            yield LintIssue(
                rule=self.id,
                severity=severity,
                message=f"Circular requirement chain: {cycle_str}",
                path="$.library",
                ref=first_ref,
            )


def collect_entity_maturities(spec: dict[str, Any]) -> dict[str, str | None]:
    """Collect maturity levels for all entities.

    Returns:
        Dict mapping entity refs to their maturity level (or None).
    """
    maturities: dict[str, str | None] = {}
    library = spec.get("library", {})

    # Types
    for type_def in library.get("types", []):
        name = type_def.get("name")
        if name:
            maturities[f"#/types/{name}"] = type_def.get("maturity")

    # Functions
    for func in library.get("functions", []):
        name = func.get("name")
        if name:
            maturities[f"#/functions/{name}"] = func.get("maturity")

    # Features
    for feature in library.get("features", []):
        fid = feature.get("id")
        if fid:
            maturities[f"#/features/{fid}"] = feature.get("maturity")

    return maturities


# Maturity level ordering for comparison
MATURITY_ORDER = {
    "idea": 0,
    "specified": 1,
    "designed": 2,
    "implemented": 3,
    "tested": 4,
    "documented": 5,
    "released": 6,
    "deprecated": 7,
}


@RuleRegistry.register
class UnsatisfiedRequirement(LintRule):
    """Required entities should meet minimum maturity constraints."""

    id = "X005"
    name = "unsatisfied-requirement"
    description = "Required entity does not meet minimum maturity level"
    default_severity = Severity.WARNING
    category = "consistency"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        severity = self.get_severity(config)
        maturities = collect_entity_maturities(spec)
        library = spec.get("library", {})

        # Check types
        for i, type_def in enumerate(library.get("types", [])):
            name = type_def.get("name")
            for j, req in enumerate(type_def.get("requires", [])):
                if not isinstance(req, dict):
                    continue
                ref = req.get("ref")
                min_maturity = req.get("min_maturity")
                if ref and min_maturity:
                    actual = maturities.get(ref)
                    if actual is None:
                        continue  # X001 handles missing refs
                    if MATURITY_ORDER.get(actual, -1) < MATURITY_ORDER.get(min_maturity, 0):
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=(
                                f"Required entity '{ref}' has maturity '{actual}' "
                                f"but needs '{min_maturity}'"
                            ),
                            path=f"$.library.types[{i}].requires[{j}]",
                            ref=f"#/types/{name}",
                        )

        # Check functions
        for i, func in enumerate(library.get("functions", [])):
            fname = func.get("name")
            for j, req in enumerate(func.get("requires", [])):
                if not isinstance(req, dict):
                    continue
                ref = req.get("ref")
                min_maturity = req.get("min_maturity")
                if ref and min_maturity:
                    actual = maturities.get(ref)
                    if actual is None:
                        continue
                    if MATURITY_ORDER.get(actual, -1) < MATURITY_ORDER.get(min_maturity, 0):
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=(
                                f"Required entity '{ref}' has maturity '{actual}' "
                                f"but needs '{min_maturity}'"
                            ),
                            path=f"$.library.functions[{i}].requires[{j}]",
                            ref=f"#/functions/{fname}",
                        )

        # Check features
        for i, feature in enumerate(library.get("features", [])):
            fid = feature.get("id")
            for j, req in enumerate(feature.get("requires", [])):
                if not isinstance(req, dict):
                    continue
                ref = req.get("ref")
                min_maturity = req.get("min_maturity")
                if ref and min_maturity:
                    actual = maturities.get(ref)
                    if actual is None:
                        continue
                    if MATURITY_ORDER.get(actual, -1) < MATURITY_ORDER.get(min_maturity, 0):
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=(
                                f"Required entity '{ref}' has maturity '{actual}' "
                                f"but needs '{min_maturity}'"
                            ),
                            path=f"$.library.features[{i}].requires[{j}]",
                            ref=f"#/features/{fid}",
                        )


# Pydantic base classes that are incompatible with kind: dataclass
PYDANTIC_BASE_CLASSES = {"BaseModel", "RootModel", "BaseSettings"}


@RuleRegistry.register
class MixedDataclassPydantic(LintRule):
    """Types with kind: dataclass should not inherit from Pydantic base classes."""

    id = "X007"
    name = "mixed-dataclass-pydantic"
    description = "Type has kind: dataclass but inherits from Pydantic base class"
    default_severity = Severity.ERROR
    category = "consistency"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        types = spec.get("library", {}).get("types", [])
        severity = self.get_severity(config)

        for i, type_def in enumerate(types):
            kind = type_def.get("kind")
            bases = set(type_def.get("bases", []))
            name = type_def.get("name", "?")

            # Check if kind is dataclass but bases include a Pydantic class
            if kind == "dataclass":
                pydantic_bases = bases & PYDANTIC_BASE_CLASSES
                if pydantic_bases:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Type '{name}' has kind: dataclass but inherits from "
                            f"Pydantic class(es): {', '.join(sorted(pydantic_bases))}. "
                            f"Use kind: class or remove Pydantic bases."
                        ),
                        path=f"$.library.types[{i}]",
                        ref=f"#/types/{name}",
                    )
