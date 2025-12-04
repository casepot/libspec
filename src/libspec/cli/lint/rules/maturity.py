"""Maturity lint rules (M001-M099).

Rules for validating maturity tracking and status consistency.
"""

from typing import Any, Iterator

from typing_extensions import override

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry


# Mapping from maturity to expected FeatureStatus
# idea, specified, designed -> planned
# implemented -> implemented
# tested, documented, released, deprecated -> tested
MATURITY_TO_STATUS = {
    "idea": "planned",
    "specified": "planned",
    "designed": "planned",
    "implemented": "implemented",
    "tested": "tested",
    "documented": "tested",
    "released": "tested",
    "deprecated": "tested",
}


@RuleRegistry.register
class MaturityStatusMismatch(LintRule):
    """Feature maturity should be consistent with status."""

    id = "M001"
    name = "maturity-status-mismatch"
    description = "Feature maturity is inconsistent with its status"
    default_severity = Severity.WARNING
    category = "maturity"

    @override
    def check(self, spec: dict[str, Any], config: dict[str, Any]) -> Iterator[LintIssue]:
        features = spec.get("library", {}).get("features", [])
        severity = self.get_severity(config)

        for i, feature in enumerate(features):
            maturity = feature.get("maturity")
            status = feature.get("status", "planned")
            fid = feature.get("id", "?")

            # Skip if maturity is not set
            if maturity is None:
                continue

            # Check if maturity matches expected status
            expected_status = MATURITY_TO_STATUS.get(maturity)
            if expected_status and expected_status != status:
                yield LintIssue(
                    rule=self.id,
                    severity=severity,
                    message=(
                        f"Feature '{fid}' has maturity '{maturity}' which implies "
                        f"status '{expected_status}', but status is '{status}'"
                    ),
                    path=f"$.library.features[{i}]",
                    ref=f"#/features/{fid}",
                    suggested_fix=f"Change status to '{expected_status}' or update maturity",
                )
