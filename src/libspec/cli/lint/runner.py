"""Lint runner - executes rules against specs."""

from typing import Any

from libspec.cli.lint.base import LintIssue, LintRule, Severity
from libspec.cli.lint.registry import RuleRegistry
from libspec.cli.config import LintConfig


class LintRunner:
    """Runs lint rules against a spec."""

    def __init__(self, config: LintConfig | None = None):
        """
        Initialize the runner.

        Args:
            config: Lint configuration (uses defaults if None)
        """
        self.config = config or LintConfig()

    def run(
        self,
        spec: dict[str, Any],
        rule_ids: list[str] | None = None,
        min_severity: Severity | None = None,
    ) -> list[LintIssue]:
        """
        Run lint rules against a spec.

        Args:
            spec: The spec data to lint
            rule_ids: Specific rules to run (runs all if None)
            min_severity: Minimum severity to include in results

        Returns:
            List of issues found
        """
        issues: list[LintIssue] = []

        # Get rules to run
        if rule_ids:
            rule_classes = [
                RuleRegistry.get_rule(rid)
                for rid in rule_ids
                if RuleRegistry.get_rule(rid)
            ]
        else:
            rule_classes = RuleRegistry.get_all_rules()

        # Run each enabled rule
        config_dict = self.config.model_dump()
        for rule_class in rule_classes:
            if rule_class is None:
                continue

            # Check if rule is enabled
            if not self.config.is_rule_enabled(rule_class.id, rule_class.category):
                continue

            # Instantiate and run rule
            rule = rule_class()
            for issue in rule.check(spec, config_dict):
                # Apply severity filter
                if min_severity:
                    severity_order = {
                        Severity.ERROR: 0,
                        Severity.WARNING: 1,
                        Severity.INFO: 2,
                    }
                    if severity_order.get(issue.severity, 2) > severity_order.get(
                        min_severity, 2
                    ):
                        continue
                issues.append(issue)

        return issues

    def get_available_rules(self) -> list[dict[str, Any]]:
        """Get information about all available rules."""
        rules = []
        for rule_class in RuleRegistry.get_all_rules():
            rules.append(
                {
                    "id": rule_class.id,
                    "name": rule_class.name,
                    "description": rule_class.description,
                    "category": rule_class.category,
                    "default_severity": rule_class.default_severity.value,
                    "enabled": self.config.is_rule_enabled(
                        rule_class.id, rule_class.category
                    ),
                }
            )
        return sorted(rules, key=lambda r: r["id"])
