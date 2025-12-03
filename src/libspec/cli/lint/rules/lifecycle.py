"""Lifecycle lint rules (L001-L099)."""

from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


def get_workflow_for_entity(
    entity: dict[str, Any],
    spec: dict[str, Any],
) -> dict[str, Any] | None:
    """Get the workflow spec for an entity."""
    workflow_name = entity.get("workflow") or spec.get("library", {}).get(
        "default_workflow"
    )
    if not workflow_name:
        return None
    for w in spec.get("library", {}).get("workflows", []):
        if w.get("name") == workflow_name:
            return w
    return None


def get_workflow_states(workflow: dict[str, Any]) -> set[str]:
    """Get all state names in a workflow."""
    return {s.get("name") for s in workflow.get("states", []) if s.get("name")}


@RuleRegistry.register
class InvalidLifecycleState(LintRule):
    """Entity lifecycle_state must be a valid state in its workflow."""

    id = "L001"
    name = "invalid-lifecycle-state"
    description = "Entity has lifecycle_state not defined in its workflow"
    default_severity = Severity.ERROR
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        # Check types
        for i, t in enumerate(library.get("types", [])):
            if state := t.get("lifecycle_state"):
                workflow = get_workflow_for_entity(t, spec)
                if workflow:
                    valid_states = get_workflow_states(workflow)
                    if state not in valid_states:
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=f"Type '{t.get('name')}' has invalid lifecycle_state "
                            f"'{state}' (not in workflow '{workflow.get('name')}')",
                            path=f"$.library.types[{i}].lifecycle_state",
                            ref=f"#/types/{t.get('name')}",
                        )

        # Check functions
        for i, f in enumerate(library.get("functions", [])):
            if state := f.get("lifecycle_state"):
                workflow = get_workflow_for_entity(f, spec)
                if workflow:
                    valid_states = get_workflow_states(workflow)
                    if state not in valid_states:
                        fn_name = f.get("name")
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=f"Function '{fn_name}' has invalid lifecycle_state '{state}'",
                            path=f"$.library.functions[{i}].lifecycle_state",
                            ref=f"#/functions/{fn_name}",
                        )

        # Check features
        for i, feat in enumerate(library.get("features", [])):
            if state := feat.get("lifecycle_state"):
                workflow = get_workflow_for_entity(feat, spec)
                if workflow:
                    valid_states = get_workflow_states(workflow)
                    if state not in valid_states:
                        feat_id = feat.get("id")
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=f"Feature '{feat_id}' has invalid lifecycle_state '{state}'",
                            path=f"$.library.features[{i}].lifecycle_state",
                            ref=f"#/features/{feat_id}",
                        )

        # Check methods in types
        for ti, t in enumerate(library.get("types", [])):
            for mi, m in enumerate(t.get("methods", [])):
                if state := m.get("lifecycle_state"):
                    workflow = get_workflow_for_entity(m, spec)
                    if not workflow:
                        workflow = get_workflow_for_entity(t, spec)
                    if workflow:
                        valid_states = get_workflow_states(workflow)
                        if state not in valid_states:
                            tname = t.get("name")
                            mname = m.get("name")
                            yield LintIssue(
                                rule=self.id,
                                severity=severity,
                                message=(
                                    f"Method '{tname}.{mname}' has invalid "
                                    f"lifecycle_state '{state}'"
                                ),
                                path=f"$.library.types[{ti}].methods[{mi}].lifecycle_state",
                                ref=f"#/types/{tname}/methods/{mname}",
                            )


@RuleRegistry.register
class MissingRequiredEvidence(LintRule):
    """Entity at a state must have required evidence for that state."""

    id = "L002"
    name = "missing-required-evidence"
    description = "Entity missing required evidence for its lifecycle state"
    default_severity = Severity.WARNING
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        def check_entity(
            entity: dict[str, Any],
            entity_type: str,
            index: int,
            ref: str,
        ) -> Iterator[LintIssue]:
            state = entity.get("lifecycle_state")
            if not state:
                return

            workflow = get_workflow_for_entity(entity, spec)
            if not workflow:
                return

            # Find the state spec
            state_spec = None
            for s in workflow.get("states", []):
                if s.get("name") == state:
                    state_spec = s
                    break

            if not state_spec:
                return

            required_evidence = state_spec.get("required_evidence", [])
            if not required_evidence:
                return

            # Check what evidence exists
            evidence = entity.get("state_evidence", [])
            evidence_types = {e.get("type") for e in evidence}

            missing = [req for req in required_evidence if req not in evidence_types]
            if missing:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"{entity_type.title()} '{entity.get('name') or entity.get('id')}' "
                    f"missing required evidence for state '{state}': {', '.join(missing)}",
                    path=f"$.library.{entity_type}s[{index}].state_evidence",
                    ref=ref,
                )

        # Check all entity types
        for i, t in enumerate(library.get("types", [])):
            yield from check_entity(t, "type", i, f"#/types/{t.get('name')}")

        for i, f in enumerate(library.get("functions", [])):
            yield from check_entity(f, "function", i, f"#/functions/{f.get('name')}")

        for i, feat in enumerate(library.get("features", [])):
            yield from check_entity(feat, "feature", i, f"#/features/{feat.get('id')}")


@RuleRegistry.register
class DanglingWorkflowReference(LintRule):
    """Entity workflow reference must point to a defined workflow."""

    id = "L003"
    name = "dangling-workflow-reference"
    description = "Entity references undefined workflow"
    default_severity = Severity.ERROR
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        defined_workflows = {w.get("name") for w in library.get("workflows", [])}

        def check_workflow_ref(
            entity: dict[str, Any],
            entity_type: str,
            index: int,
            ref: str,
        ) -> Iterator[LintIssue]:
            workflow = entity.get("workflow")
            if workflow and workflow not in defined_workflows:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"{entity_type.title()} references undefined workflow '{workflow}'",
                    path=f"$.library.{entity_type}s[{index}].workflow",
                    ref=ref,
                )

        for i, t in enumerate(library.get("types", [])):
            yield from check_workflow_ref(t, "type", i, f"#/types/{t.get('name')}")

        for i, f in enumerate(library.get("functions", [])):
            yield from check_workflow_ref(f, "function", i, f"#/functions/{f.get('name')}")

        for i, feat in enumerate(library.get("features", [])):
            yield from check_workflow_ref(feat, "feature", i, f"#/features/{feat.get('id')}")


@RuleRegistry.register
class LifecycleFeatureStatusMismatch(LintRule):
    """Feature lifecycle_state should be consistent with features.status."""

    id = "L004"
    name = "lifecycle-feature-status-mismatch"
    description = "Feature lifecycle_state inconsistent with status field"
    default_severity = Severity.INFO
    category = "lifecycle"

    # Default mapping from lifecycle states to feature status
    STATE_TO_STATUS: dict[str, str] = {
        "idea": "planned",
        "drafted": "planned",
        "reviewed": "planned",
        "approved": "planned",
        "implemented": "implemented",
        "tested": "tested",
        "documented": "tested",
        "released": "tested",
        "deprecated": "tested",
        "removed": "tested",
    }

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        for i, feat in enumerate(library.get("features", [])):
            lifecycle_state = feat.get("lifecycle_state")
            status = feat.get("status", "planned")

            if lifecycle_state:
                expected_status = self.STATE_TO_STATUS.get(lifecycle_state)
                if expected_status and expected_status != status:
                    feat_id = feat.get("id")
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Feature '{feat_id}' has lifecycle_state "
                            f"'{lifecycle_state}' but status '{status}' "
                            f"(expected '{expected_status}')"
                        ),
                        path=f"$.library.features[{i}]",
                        ref=f"#/features/{feat_id}",
                    )


@RuleRegistry.register
class InvalidWorkflowDefinition(LintRule):
    """Workflow definitions must be internally consistent."""

    id = "L005"
    name = "invalid-workflow-definition"
    description = "Workflow has invalid state or transition references"
    default_severity = Severity.ERROR
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        for i, wf in enumerate(library.get("workflows", [])):
            wf_name = wf.get("name", f"workflow[{i}]")
            state_names = get_workflow_states(wf)

            # Check initial_state exists
            initial = wf.get("initial_state")
            if initial and initial not in state_names:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=f"Workflow '{wf_name}' has invalid initial_state '{initial}'",
                    path=f"$.library.workflows[{i}].initial_state",
                    ref=f"#/workflows/{wf_name}",
                )

            # Check transitions reference valid states
            for j, t in enumerate(wf.get("transitions", [])):
                from_state = t.get("from_state")
                to_state = t.get("to_state")

                if from_state and from_state not in state_names:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Workflow '{wf_name}' transition has invalid "
                            f"from_state '{from_state}'"
                        ),
                        path=f"$.library.workflows[{i}].transitions[{j}].from_state",
                        ref=f"#/workflows/{wf_name}",
                    )

                if to_state and to_state not in state_names:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Workflow '{wf_name}' transition has invalid "
                            f"to_state '{to_state}'"
                        ),
                        path=f"$.library.workflows[{i}].transitions[{j}].to_state",
                        ref=f"#/workflows/{wf_name}",
                    )


def get_custom_evidence_types(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Get all custom evidence types defined across workflows."""
    custom_types: dict[str, dict[str, Any]] = {}
    library = spec.get("library", {})
    for wf in library.get("workflows", []):
        for et in wf.get("evidence_types", []):
            name = et.get("name")
            if name:
                custom_types[name] = et
    return custom_types


def is_valid_url(reference: str) -> bool:
    """Check if reference looks like a valid URL."""
    from urllib.parse import urlparse
    try:
        result = urlparse(reference)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


# Type-specific required fields
EVIDENCE_REQUIRED_FIELDS: dict[str, list[str]] = {
    "pr": ["url"],
    "tests": ["path"],
    "design_doc": ["reference"],
    "docs": ["url"],
    "approval": ["reference", "author"],
    "benchmark": ["reference"],
    "migration_guide": ["reference"],
    "deprecation_notice": ["reference", "date"],
    "custom": ["type_name"],
}


def iter_entities_with_evidence(
    spec: dict[str, Any],
) -> Iterator[tuple[str, int, str, dict[str, Any], int, dict[str, Any]]]:
    """Yield (entity_type, index, name/id, entity, evidence_index, evidence)."""
    library = spec.get("library", {})

    for i, t in enumerate(library.get("types", [])):
        for j, ev in enumerate(t.get("state_evidence", [])):
            yield ("types", i, t.get("name", "?"), t, j, ev)

    for i, f in enumerate(library.get("functions", [])):
        for j, ev in enumerate(f.get("state_evidence", [])):
            yield ("functions", i, f.get("name", "?"), f, j, ev)

    for i, feat in enumerate(library.get("features", [])):
        for j, ev in enumerate(feat.get("state_evidence", [])):
            yield ("features", i, feat.get("id", "?"), feat, j, ev)

    # Methods in types
    for ti, t in enumerate(library.get("types", [])):
        for mi, m in enumerate(t.get("methods", [])):
            for j, ev in enumerate(m.get("state_evidence", [])):
                tname = t.get("name", "?")
                mname = m.get("name", "?")
                yield (
                    f"types[{ti}].methods",
                    mi,
                    f"{tname}.{mname}",
                    m,
                    j,
                    ev,
                )


@RuleRegistry.register
class InvalidEvidenceReference(LintRule):
    """Evidence reference format should match expected pattern for its type."""

    id = "L006"
    name = "invalid-evidence-reference"
    description = "Evidence reference format invalid for its type"
    default_severity = Severity.WARNING
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        severity = self.get_severity(config)
        custom_types = get_custom_evidence_types(spec)

        for entity_type, idx, name, _entity, ev_idx, evidence in iter_entities_with_evidence(spec):
            ev_type = evidence.get("type")

            # PR evidence should have valid URL
            if ev_type == "pr":
                url = evidence.get("url")
                if url and not is_valid_url(url):
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"PR evidence for '{name}' has invalid URL: {url}",
                        path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].url",
                        ref=f"#/{entity_type}/{name}",
                    )

            # Docs evidence should have valid URL
            elif ev_type == "docs":
                url = evidence.get("url")
                if url and not is_valid_url(url):
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=f"Docs evidence for '{name}' has invalid URL: {url}",
                        path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].url",
                        ref=f"#/{entity_type}/{name}",
                    )

            # Custom evidence - check against workflow-defined patterns
            elif ev_type == "custom":
                type_name = evidence.get("type_name")
                if type_name and type_name in custom_types:
                    type_def = custom_types[type_name]
                    ref_pattern = type_def.get("reference_pattern")
                    reference = evidence.get("reference")
                    if ref_pattern and reference:
                        import re
                        if not re.match(ref_pattern, reference):
                            yield LintIssue(
                                rule=self.id,
                                severity=severity,
                                message=(
                                    f"Custom evidence '{type_name}' for '{name}' "
                                    f"reference doesn't match pattern: {ref_pattern}"
                                ),
                                path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].reference",
                                ref=f"#/{entity_type}/{name}",
                            )

                    # Check url_pattern if defined
                    url_pattern = type_def.get("url_pattern")
                    url = evidence.get("url")
                    if url_pattern and url:
                        import re
                        if not re.match(url_pattern, url):
                            yield LintIssue(
                                rule=self.id,
                                severity=severity,
                                message=(
                                    f"Custom evidence '{type_name}' for '{name}' "
                                    f"URL doesn't match pattern: {url_pattern}"
                                ),
                                path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].url",
                                ref=f"#/{entity_type}/{name}",
                            )


@RuleRegistry.register
class UndefinedCustomEvidenceType(LintRule):
    """Custom evidence type must be defined in workflow."""

    id = "L007"
    name = "undefined-custom-evidence-type"
    description = "Custom evidence references undefined type"
    default_severity = Severity.ERROR
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        severity = self.get_severity(config)
        custom_types = get_custom_evidence_types(spec)

        for entity_type, idx, name, _entity, ev_idx, evidence in iter_entities_with_evidence(spec):
            ev_type = evidence.get("type")

            if ev_type == "custom":
                type_name = evidence.get("type_name")
                if type_name and type_name not in custom_types:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Custom evidence for '{name}' references undefined "
                            f"type '{type_name}'"
                        ),
                        path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].type_name",
                        ref=f"#/{entity_type}/{name}",
                    )


@RuleRegistry.register
class EvidenceMissingRequiredField(LintRule):
    """Evidence must have required fields for its type."""

    id = "L008"
    name = "evidence-missing-required-field"
    description = "Evidence missing required field for its type"
    default_severity = Severity.WARNING
    category = "lifecycle"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        if "lifecycle" not in spec.get("extensions", []):
            return

        severity = self.get_severity(config)
        custom_types = get_custom_evidence_types(spec)

        for entity_type, idx, name, _entity, ev_idx, evidence in iter_entities_with_evidence(spec):
            ev_type = evidence.get("type")
            if not ev_type:
                continue

            # Get required fields for this type
            if ev_type == "custom":
                type_name = evidence.get("type_name")
                if type_name and type_name in custom_types:
                    type_def = custom_types[type_name]
                    required = type_def.get("required_fields", [])
                else:
                    required = EVIDENCE_REQUIRED_FIELDS.get("custom", [])
            else:
                required = EVIDENCE_REQUIRED_FIELDS.get(ev_type, [])

            # Check each required field
            for field in required:
                if not evidence.get(field):
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Evidence type '{ev_type}' for '{name}' "
                            f"missing required field '{field}'"
                        ),
                        path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}]",
                        ref=f"#/{entity_type}/{name}",
                    )


@RuleRegistry.register
class InvalidTestPathPattern(LintRule):
    """Test evidence path should look like a test file or directory."""

    id = "L009"
    name = "invalid-test-path-pattern"
    description = "Test evidence path doesn't look like a test file"
    default_severity = Severity.INFO
    category = "lifecycle"

    # Common test path patterns
    TEST_PATTERNS = [
        r".*test.*",  # Contains 'test'
        r".*spec.*",  # Contains 'spec' (JS/Ruby style)
        r".*_test\.(py|go|rs|js|ts)$",  # file_test.ext
        r".*\.test\.(js|ts|jsx|tsx)$",  # file.test.js
        r".*\.spec\.(js|ts|jsx|tsx)$",  # file.spec.js
        r"tests?/.*",  # tests/ or test/ directory
        r"__tests__/.*",  # Jest style
        r".*_spec\.rb$",  # Ruby RSpec
    ]

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        import re

        if "lifecycle" not in spec.get("extensions", []):
            return

        severity = self.get_severity(config)

        for entity_type, idx, name, _entity, ev_idx, evidence in iter_entities_with_evidence(spec):
            ev_type = evidence.get("type")

            if ev_type == "tests":
                path = evidence.get("path", "")
                if path:
                    # Check if path matches any known test pattern
                    matches_pattern = any(
                        re.search(pattern, path, re.IGNORECASE)
                        for pattern in self.TEST_PATTERNS
                    )
                    if not matches_pattern:
                        yield LintIssue(
                            rule=self.id,
                            severity=severity,
                            message=(
                                f"Test evidence for '{name}' has path '{path}' "
                                "which doesn't match common test file patterns"
                            ),
                            path=f"$.library.{entity_type}[{idx}].state_evidence[{ev_idx}].path",
                            ref=f"#/{entity_type}/{name}",
                        )
