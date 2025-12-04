"""Cross-extension lint rules (E001-E099).

These rules detect semantic conflicts and inconsistencies between extensions
when multiple extensions are enabled in a spec.
"""

from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


@RuleRegistry.register
class WorkflowTestingMismatch(LintRule):
    """Entity with 'tested' workflow_state should have testing extension specs."""

    id = "E001"
    name = "workflow-testing-mismatch"
    description = "Tested entity missing test coverage specs from testing extension"
    default_severity = Severity.WARNING
    category = "extension"

    # Workflow states that imply testing should be documented
    TESTED_STATES = {"tested", "documented", "released"}

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        extensions = spec.get("extensions", [])
        if "workflow" not in extensions or "testing" not in extensions:
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        # Check types
        for i, t in enumerate(library.get("types", [])):
            workflow_state = t.get("workflow_state")
            if workflow_state in self.TESTED_STATES:
                test_coverage = t.get("test_coverage")
                if not test_coverage:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Type '{t.get('name')}' has workflow_state "
                            f"'{workflow_state}' but no test_coverage defined"
                        ),
                        path=f"$.library.types[{i}]",
                        ref=f"#/types/{t.get('name')}",
                    )

        # Check features
        for i, feat in enumerate(library.get("features", [])):
            workflow_state = feat.get("workflow_state")
            if workflow_state in self.TESTED_STATES:
                test_coverage = feat.get("test_coverage")
                if not test_coverage:
                    yield LintIssue(
                        rule=self.id,
                        severity=severity,
                        message=(
                            f"Feature '{feat.get('id')}' has workflow_state "
                            f"'{workflow_state}' but no test_coverage defined"
                        ),
                        path=f"$.library.features[{i}]",
                        ref=f"#/features/{feat.get('id')}",
                    )


@RuleRegistry.register
class PlannedWithImplementationEvidence(LintRule):
    """Entity in early workflow state should not have implementation evidence."""

    id = "E002"
    name = "planned-with-implementation-evidence"
    description = "Planned entity has implementation evidence (may indicate stale state)"
    default_severity = Severity.INFO
    category = "extension"

    # Early workflow states where implementation evidence is unexpected
    EARLY_STATES = {"idea", "drafted", "planned"}

    # Evidence types that suggest implementation work
    IMPLEMENTATION_EVIDENCE = {"pr", "tests", "benchmark"}

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        extensions = spec.get("extensions", [])
        if "workflow" not in extensions:
            return

        library = spec.get("library", {})
        severity = self.get_severity(config)

        def check_entity(
            entity: dict[str, Any],
            entity_type: str,
            index: int,
            name: str,
        ) -> Iterator[LintIssue]:
            workflow_state = entity.get("workflow_state")
            if workflow_state not in self.EARLY_STATES:
                return

            evidence = entity.get("state_evidence", [])
            impl_evidence = [
                e for e in evidence if e.get("type") in self.IMPLEMENTATION_EVIDENCE
            ]
            if impl_evidence:
                evidence_types = ", ".join(e.get("type") for e in impl_evidence)
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=(
                        f"{entity_type.title()} '{name}' has workflow_state "
                        f"'{workflow_state}' but has implementation evidence "
                        f"({evidence_types}) - consider updating workflow_state"
                    ),
                    path=f"$.library.{entity_type}s[{index}]",
                    ref=f"#/{entity_type}s/{name}",
                )

        for i, t in enumerate(library.get("types", [])):
            yield from check_entity(t, "type", i, t.get("name", "?"))

        for i, f in enumerate(library.get("functions", [])):
            yield from check_entity(f, "function", i, f.get("name", "?"))

        for i, feat in enumerate(library.get("features", [])):
            yield from check_entity(feat, "feature", i, feat.get("id", "?"))
