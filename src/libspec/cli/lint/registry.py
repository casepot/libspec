"""Lint rule registry."""

from typing import Type

from libspec.cli.lint.base import LintRule


class RuleRegistry:
    """Registry of all available lint rules."""

    _rules: dict[str, Type[LintRule]] = {}

    @classmethod
    def register(cls, rule_class: Type[LintRule]) -> Type[LintRule]:
        """
        Decorator to register a rule.

        Usage:
            @RuleRegistry.register
            class MyRule(LintRule):
                ...
        """
        cls._rules[rule_class.id] = rule_class
        return rule_class

    @classmethod
    def get_rule(cls, rule_id: str) -> Type[LintRule] | None:
        """Get a rule class by ID."""
        return cls._rules.get(rule_id)

    @classmethod
    def get_all_rules(cls) -> list[Type[LintRule]]:
        """Get all registered rule classes."""
        return list(cls._rules.values())

    @classmethod
    def get_rules_by_category(cls, category: str) -> list[Type[LintRule]]:
        """Get all rules in a category."""
        return [r for r in cls._rules.values() if r.category == category]

    @classmethod
    def get_rule_ids(cls) -> list[str]:
        """Get all registered rule IDs."""
        return list(cls._rules.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules (for testing)."""
        cls._rules.clear()
