"""Validate commands: validate, lint."""

import sys

import click

from libspec.cli.app import Context, pass_context

# Import rules to trigger registration via side effect
from libspec.cli.lint import rules as _rules  # noqa: F401

del _rules  # Not directly used, imported for side effect
from libspec.cli.lint.base import Severity
from libspec.cli.lint.runner import LintRunner
from libspec.cli.output import make_envelope, output_json, output_text_lint, output_text_validate


@click.command()
@click.option("--strict", is_flag=True, help="Exit code 3 on validation failure")
@pass_context
def validate(ctx: Context, strict: bool) -> None:
    """
    Validate spec against JSON Schema.

    \b
    Checks structural validity against the libspec schema.
    For semantic checks (naming, completeness), use 'lint'.

    \b
    Examples:
        libspec validate
        libspec validate --strict && echo "Valid!"
    """
    from libspec import validate_spec as do_validate

    spec = ctx.get_spec()

    errors: list[str] = do_validate(spec.path)  # type: ignore[assignment]
    valid = len(errors) == 0

    if ctx.text:
        output_text_validate(errors, valid)
    else:
        envelope = make_envelope(
            "validate",
            spec,
            {"valid": valid, "errors": errors},
            meta={"error_count": len(errors)},
        )
        output_json(envelope, ctx.no_meta)

    if strict and not valid:
        sys.exit(3)


@click.command()
@click.option(
    "--rule", "-r", multiple=True, help="Run specific rule(s) only (e.g., -r S001 -r N001)"
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["error", "warning", "info"]),
    help="Minimum severity to report",
)
@click.option("--strict", is_flag=True, help="Exit code 4 if any issues found")
@click.option("--list-rules", is_flag=True, help="List all available lint rules")
@pass_context
def lint(
    ctx: Context,
    rule: tuple[str, ...],
    severity: str | None,
    strict: bool,
    list_rules: bool,
) -> None:
    """
    Run semantic linting on the spec.

    \b
    Checks for issues beyond schema validity:
      - Structural (S): Missing descriptions, orphan refs
      - Naming (N): Kebab-case IDs, PascalCase types
      - Completeness (C): Features without steps
      - Consistency (X): Dangling refs, duplicates

    \b
    Configure in pyproject.toml:
        [tool.libspec.lint]
        disable = ["C007"]
        [tool.libspec.lint.rules]
        S001 = "warning"

    \b
    Examples:
        libspec lint
        libspec lint --strict
        libspec lint -r S001 -r S002
        libspec lint --severity error
        libspec lint --list-rules
    """
    runner = LintRunner(ctx.config.lint)

    # List rules mode
    if list_rules:
        rules = runner.get_available_rules()
        if ctx.text:
            for r in rules:
                enabled = "+" if r["enabled"] else "-"
                click.echo(
                    f"{enabled} {r['id']} {r['category']} {r['default_severity']} {r['name']}"
                )
            click.echo("---")
            click.echo(f"{len(rules)} rules")
        else:
            envelope_data = {
                "libspec_cli": "0.1.0",
                "command": "lint --list-rules",
                "result": rules,
                "meta": {"count": len(rules)},
            }
            click.echo(click.style("", reset=True), nl=False)
            import json
            print(json.dumps(envelope_data, indent=2))
        return

    spec = ctx.get_spec()

    # Determine severity filter
    min_severity = None
    if severity:
        min_severity = Severity(severity)

    # Run lint
    rule_ids = list(rule) if rule else None
    issues = runner.run(spec.data, rule_ids=rule_ids, min_severity=min_severity)

    passed = len(issues) == 0

    # Compute metadata
    by_severity: dict[str, int] = {}
    by_rule: dict[str, int] = {}
    for issue in issues:
        sev = issue.severity.value
        by_severity[sev] = by_severity.get(sev, 0) + 1
        by_rule[issue.rule] = by_rule.get(issue.rule, 0) + 1

    if ctx.text:
        output_text_lint([i.model_dump(exclude_none=True) for i in issues], passed)
    else:
        envelope = make_envelope(
            "lint",
            spec,
            {
                "passed": passed,
                "issues": [i.model_dump(exclude_none=True) for i in issues],
            },
            meta={
                "total": len(issues),
                "by_severity": by_severity,
                "by_rule": by_rule,
            },
        )
        output_json(envelope, ctx.no_meta)

    if strict and not passed:
        sys.exit(4)
