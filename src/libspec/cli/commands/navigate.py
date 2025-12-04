"""Navigation commands: next, blocked, gaps, progress.

These commands answer development workflow questions:
- What's ready to work on next?
- What's blocked and why?
- What gaps exist in the current state?
- What's the overall progress?
"""

from collections import defaultdict
from typing import Any, TypedDict

import click

from libspec.cli.app import Context, pass_context
from libspec.cli.lifecycle_utils import (
    MATURITY_ORDER,
    check_gates_satisfied,
    check_requirement_satisfied,
    collect_entities_with_tracking,
    collect_entity_maturities,
    get_entity_state,
    get_maturity_gate,
    get_next_maturity,
    get_valid_next_states,
    get_workflow_spec,
)
from libspec.cli.output import make_envelope, output_json


class NextItem(TypedDict):
    """An entity ready to advance."""

    entity_type: str
    name: str
    ref: str
    current_state: str
    next_state: str


class BlockedItem(TypedDict):
    """An entity blocked from advancing."""

    entity_type: str
    name: str
    ref: str
    current_state: str
    next_state: str
    reasons: list[str]


class GapItem(TypedDict):
    """An entity missing expected information."""

    entity_type: str
    name: str
    ref: str
    current_state: str | None
    gap_type: str
    message: str


@click.command()
@click.option("--type", "-t", "entity_type", type=click.Choice(["type", "function", "feature", "method", "all"]),
              default="all", help="Filter by entity type")
@click.option("--maturity", "-m", help="Filter by current maturity level")
@click.option("--workflow", "-w", help="Filter by workflow (for legacy state mode)")
@click.option("--module", help="Filter by module (regex pattern)")
@click.option("--limit", "-n", type=int, default=20, help="Limit number of results")
@pass_context
def next_cmd(
    ctx: Context,
    entity_type: str,
    maturity: str | None,
    workflow: str | None,
    module: str | None,
    limit: int,
) -> None:
    """Show entities ready to advance to next maturity level.

    Lists entities that have satisfied all gates/requirements for
    advancement to the next development stage.

    \b
    Examples:
        libspec next                     # All ready entities
        libspec next -t feature          # Features ready to advance
        libspec next -m designed         # Entities at 'designed' stage
        libspec next -n 10               # Limit to 10 results
    """
    import re

    spec = ctx.get_spec()
    entities = collect_entities_with_tracking(spec.data)
    entity_maturities = collect_entity_maturities(spec.data)
    default_workflow = spec.data.get("library", {}).get("default_workflow")

    # Apply filters
    if entity_type != "all":
        entities = [e for e in entities if e.get("entity_type") == entity_type]

    if maturity:
        entities = [e for e in entities if get_entity_state(e) == maturity]

    if workflow:
        entities = [e for e in entities if (e.get("workflow") or default_workflow) == workflow]

    if module:
        pattern = re.compile(module)
        # Filter by module path in ref (e.g., #/types/Module.Class)
        entities = [e for e in entities if pattern.search(e.get("name", "") or "")]

    # Find entities ready to advance
    ready_items: list[NextItem] = []

    for entity in entities:
        current = get_entity_state(entity)
        if not current:
            continue

        # Get next state (maturity-based)
        next_state = get_next_maturity(current)
        if not next_state:
            continue  # At terminal state

        # Check gates if workflow defined
        wf_name = entity.get("workflow") or default_workflow
        wf = get_workflow_spec(wf_name, spec.data) if wf_name else None

        gate_satisfied = True
        if wf:
            gate = get_maturity_gate(current, next_state, wf)
            if gate:
                gate_status = check_gates_satisfied(entity, gate)
                unsatisfied = [g for g in gate_status if g["required"] and not g["satisfied"]]
                if unsatisfied:
                    gate_satisfied = False

        # Check requirements
        reqs_satisfied = True
        for req in spec.data.get("library", {}).get("types", []) + \
                    spec.data.get("library", {}).get("functions", []) + \
                    spec.data.get("library", {}).get("features", []):
            if req.get("name") == entity.get("name") or req.get("id") == entity.get("name"):
                for r in req.get("requires", []):
                    satisfied, _ = check_requirement_satisfied(r, entity_maturities)
                    if not satisfied:
                        reqs_satisfied = False
                        break
                break

        if gate_satisfied and reqs_satisfied:
            ready_items.append({
                "entity_type": entity.get("entity_type", ""),
                "name": entity.get("name", ""),
                "ref": entity.get("ref", ""),
                "current_state": current,
                "next_state": next_state,
            })

    # Apply limit
    ready_items = ready_items[:limit]

    # Output
    if ctx.text:
        for item in ready_items:
            click.echo(f"NEXT {item['entity_type']} {item['name']} ({item['current_state']} -> {item['next_state']})")
        click.echo("---")
        click.echo(f"{len(ready_items)} entities ready to advance")
        return

    envelope = make_envelope(
        "next",
        spec,
        {"items": ready_items},
        meta={"count": len(ready_items), "limit": limit},
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option("--type", "-t", "entity_type", type=click.Choice(["type", "function", "feature", "method", "all"]),
              default="all", help="Filter by entity type")
@click.option("--maturity", "-m", help="Filter by current maturity level")
@click.option("--gate", "-g", help="Filter by missing gate type")
@click.option("--by-requirement", is_flag=True, help="Group by blocking requirement")
@click.option("--limit", "-n", type=int, default=20, help="Limit number of results")
@pass_context
def blocked(
    ctx: Context,
    entity_type: str,
    maturity: str | None,
    gate: str | None,
    by_requirement: bool,
    limit: int,
) -> None:
    """Show entities blocked from advancing.

    Lists entities that cannot advance due to unsatisfied gates
    or unmet requirements.

    \b
    Examples:
        libspec blocked                  # All blocked entities
        libspec blocked -t feature       # Blocked features
        libspec blocked -g tests         # Blocked by tests gate
        libspec blocked --by-requirement # Group by blocking entity
    """
    spec = ctx.get_spec()
    entities = collect_entities_with_tracking(spec.data)
    entity_maturities = collect_entity_maturities(spec.data)
    default_workflow = spec.data.get("library", {}).get("default_workflow")

    # Apply filters
    if entity_type != "all":
        entities = [e for e in entities if e.get("entity_type") == entity_type]

    if maturity:
        entities = [e for e in entities if get_entity_state(e) == maturity]

    # Find blocked entities
    blocked_items: list[BlockedItem] = []

    for entity in entities:
        current = get_entity_state(entity)
        if not current:
            continue

        next_state = get_next_maturity(current)
        if not next_state:
            continue

        reasons: list[str] = []

        # Check gates
        wf_name = entity.get("workflow") or default_workflow
        wf = get_workflow_spec(wf_name, spec.data) if wf_name else None

        if wf:
            gate_def = get_maturity_gate(current, next_state, wf)
            if gate_def:
                gate_status = check_gates_satisfied(entity, gate_def)
                for gs in gate_status:
                    if gs["required"] and not gs["satisfied"]:
                        if gate is None or gate == gs["gate"]:
                            reasons.append(f"gate: {gs['gate']} not satisfied")

        # Check requirements - find entity's requirements
        library = spec.data.get("library", {})
        entity_def = None
        for t in library.get("types", []):
            if t.get("name") == entity.get("name"):
                entity_def = t
                break
        if not entity_def:
            for f in library.get("functions", []):
                if f.get("name") == entity.get("name"):
                    entity_def = f
                    break
        if not entity_def:
            for feat in library.get("features", []):
                if feat.get("id") == entity.get("name"):
                    entity_def = feat
                    break

        if entity_def:
            for r in entity_def.get("requires", []):
                satisfied, reason = check_requirement_satisfied(r, entity_maturities)
                if not satisfied and reason:
                    reasons.append(reason)

        if reasons:
            blocked_items.append({
                "entity_type": entity.get("entity_type", ""),
                "name": entity.get("name", ""),
                "ref": entity.get("ref", ""),
                "current_state": current,
                "next_state": next_state,
                "reasons": reasons,
            })

    # Apply limit
    blocked_items = blocked_items[:limit]

    # Output
    if ctx.text:
        if by_requirement:
            # Group by reason
            by_reason: dict[str, list[str]] = defaultdict(list)
            for item in blocked_items:
                for reason in item["reasons"]:
                    by_reason[reason].append(item["name"])
            for reason, names in sorted(by_reason.items()):
                click.echo(f"{reason}:")
                for name in names[:5]:
                    click.echo(f"  - {name}")
                if len(names) > 5:
                    click.echo(f"  ... and {len(names) - 5} more")
        else:
            for item in blocked_items:
                click.echo(f"BLOCKED {item['entity_type']} {item['name']} ({item['current_state']})")
                for reason in item["reasons"]:
                    click.echo(f"  - {reason}")
        click.echo("---")
        click.echo(f"{len(blocked_items)} entities blocked")
        return

    envelope = make_envelope(
        "blocked",
        spec,
        {"items": blocked_items},
        meta={"count": len(blocked_items), "limit": limit},
    )
    output_json(envelope, ctx.no_meta)


# Create a group for gaps and progress (less common commands)
@click.group()
def navigate() -> None:
    """Navigation commands for development workflow.

    \b
    Subcommands:
        gaps      Show missing information for entities
        progress  Show development progress summary
    """
    pass


@navigate.command()
@click.option("--type", "-t", "entity_type", type=click.Choice(["type", "function", "feature", "method", "all"]),
              default="all", help="Filter by entity type")
@click.option("--state", "-s", help="Filter by lifecycle/maturity state")
@click.option("--issue", "-i", type=click.Choice(["signature", "docstring", "tests", "evidence"]),
              help="Filter by gap type")
@pass_context
def gaps(
    ctx: Context,
    entity_type: str,
    state: str | None,
    issue: str | None,
) -> None:
    """Show entities missing expected information.

    Identifies gaps like missing signatures, docstrings, test evidence,
    or required evidence for the current development state.

    \b
    Gap types:
        signature   Methods/functions without signature
        docstring   Types without docstring
        tests       Entities in tested state without test evidence
        evidence    Missing required evidence for current state

    \b
    Examples:
        libspec navigate gaps                 # All gaps
        libspec navigate gaps -t type         # Gaps in types
        libspec navigate gaps -i docstring    # Missing docstrings
    """
    spec = ctx.get_spec()
    library = spec.data.get("library", {})

    gap_items: list[GapItem] = []

    # Check types
    if entity_type in ("all", "type"):
        for t in library.get("types", []):
            name = t.get("name")
            current = t.get("maturity") or t.get("lifecycle_state")

            if state and current != state:
                continue

            # Check docstring gap
            if (issue is None or issue == "docstring") and not t.get("docstring"):
                gap_items.append({
                    "entity_type": "type",
                    "name": name,
                    "ref": f"#/types/{name}",
                    "current_state": current,
                    "gap_type": "docstring",
                    "message": "Missing docstring",
                })

            # Check test evidence if tested
            if (issue is None or issue == "tests") and current in ("tested", "documented", "released"):
                has_tests = any(
                    e.get("type") == "tests"
                    for e in t.get("maturity_evidence", []) + t.get("state_evidence", [])
                )
                if not has_tests:
                    gap_items.append({
                        "entity_type": "type",
                        "name": name,
                        "ref": f"#/types/{name}",
                        "current_state": current,
                        "gap_type": "tests",
                        "message": "Marked tested but no test evidence",
                    })

    # Check functions
    if entity_type in ("all", "function"):
        for f in library.get("functions", []):
            name = f.get("name")
            current = f.get("maturity") or f.get("lifecycle_state")

            if state and current != state:
                continue

            # Check signature gap
            if (issue is None or issue == "signature") and not f.get("signature"):
                gap_items.append({
                    "entity_type": "function",
                    "name": name,
                    "ref": f"#/functions/{name}",
                    "current_state": current,
                    "gap_type": "signature",
                    "message": "Missing signature",
                })

            # Check test evidence if tested
            if (issue is None or issue == "tests") and current in ("tested", "documented", "released"):
                has_tests = any(
                    e.get("type") == "tests"
                    for e in f.get("maturity_evidence", []) + f.get("state_evidence", [])
                )
                if not has_tests:
                    gap_items.append({
                        "entity_type": "function",
                        "name": name,
                        "ref": f"#/functions/{name}",
                        "current_state": current,
                        "gap_type": "tests",
                        "message": "Marked tested but no test evidence",
                    })

    # Check methods
    if entity_type in ("all", "method"):
        for t in library.get("types", []):
            tname = t.get("name")
            for m in t.get("methods", []):
                mname = m.get("name")
                current = m.get("maturity") or m.get("lifecycle_state")

                if state and current != state:
                    continue

                # Check signature gap
                if (issue is None or issue == "signature") and not m.get("signature"):
                    gap_items.append({
                        "entity_type": "method",
                        "name": f"{tname}.{mname}",
                        "ref": f"#/types/{tname}/methods/{mname}",
                        "current_state": current,
                        "gap_type": "signature",
                        "message": "Missing signature",
                    })

    # Output
    if ctx.text:
        for item in gap_items:
            click.echo(f"GAP {item['gap_type']}: {item['entity_type']} {item['name']}")
            click.echo(f"  {item['message']}")
        click.echo("---")
        click.echo(f"{len(gap_items)} gaps found")
        return

    envelope = make_envelope(
        "gaps",
        spec,
        {"items": gap_items},
        meta={"count": len(gap_items)},
    )
    output_json(envelope, ctx.no_meta)


@navigate.command()
@click.option("--workflow", "-w", help="Filter by workflow")
@click.option("--type", "-t", "entity_type", type=click.Choice(["type", "function", "feature", "method", "all"]),
              default="all", help="Filter by entity type")
@click.option("--format", "-f", "output_format", type=click.Choice(["table", "compact", "json"]),
              default="compact", help="Output format")
@pass_context
def progress(
    ctx: Context,
    workflow: str | None,
    entity_type: str,
    output_format: str,
) -> None:
    """Show development progress summary.

    Displays entity counts by maturity level and overall statistics.

    \b
    Examples:
        libspec navigate progress              # Summary view
        libspec navigate progress -f table     # Table format
        libspec navigate progress -t feature   # Features only
    """
    spec = ctx.get_spec()
    entities = collect_entities_with_tracking(spec.data)
    default_workflow = spec.data.get("library", {}).get("default_workflow")

    # Apply filters
    if entity_type != "all":
        entities = [e for e in entities if e.get("entity_type") == entity_type]

    if workflow:
        entities = [e for e in entities if (e.get("workflow") or default_workflow) == workflow]

    # Count by state
    by_state: dict[str, int] = defaultdict(int)
    by_entity_type: dict[str, int] = defaultdict(int)
    total_tracked = len(entities)

    for entity in entities:
        state = get_entity_state(entity) or "untracked"
        by_state[state] += 1
        et = entity.get("entity_type", "unknown")
        by_entity_type[et] += 1

    # Count ready and blocked
    entity_maturities = collect_entity_maturities(spec.data)
    ready_count = 0
    blocked_count = 0

    for entity in entities:
        current = get_entity_state(entity)
        if not current:
            continue

        next_state = get_next_maturity(current)
        if not next_state:
            continue

        is_blocked = False

        # Check gates
        wf_name = entity.get("workflow") or default_workflow
        wf = get_workflow_spec(wf_name, spec.data) if wf_name else None

        if wf:
            gate = get_maturity_gate(current, next_state, wf)
            if gate:
                gate_status = check_gates_satisfied(entity, gate)
                if any(g["required"] and not g["satisfied"] for g in gate_status):
                    is_blocked = True

        # Check requirements (simplified check)
        if not is_blocked:
            library = spec.data.get("library", {})
            for coll in [library.get("types", []), library.get("functions", []), library.get("features", [])]:
                for item in coll:
                    if item.get("name") == entity.get("name") or item.get("id") == entity.get("name"):
                        for r in item.get("requires", []):
                            satisfied, _ = check_requirement_satisfied(r, entity_maturities)
                            if not satisfied:
                                is_blocked = True
                                break
                        break
                if is_blocked:
                    break

        if is_blocked:
            blocked_count += 1
        else:
            ready_count += 1

    # Output
    if ctx.text or output_format == "compact":
        # Compact single-line summary
        parts = []
        for m in MATURITY_ORDER:
            if by_state.get(m, 0) > 0:
                parts.append(f"{m}: {by_state[m]}")
        click.echo(" | ".join(parts) if parts else "No tracked entities")
        click.echo("---")
        click.echo(f"{total_tracked} tracked, {ready_count} ready, {blocked_count} blocked")
        return

    if output_format == "table":
        # Table format
        click.echo(f"{'State':<15} {'Count':>6}")
        click.echo("-" * 22)
        for m in MATURITY_ORDER:
            if by_state.get(m, 0) > 0:
                click.echo(f"{m:<15} {by_state[m]:>6}")
        click.echo("-" * 22)
        click.echo(f"{'Total':<15} {total_tracked:>6}")
        click.echo(f"{'Ready':<15} {ready_count:>6}")
        click.echo(f"{'Blocked':<15} {blocked_count:>6}")
        return

    # JSON format
    envelope = make_envelope(
        "progress",
        spec,
        {
            "by_state": dict(by_state),
            "by_entity_type": dict(by_entity_type),
            "ready_count": ready_count,
            "blocked_count": blocked_count,
        },
        meta={"total": total_tracked},
    )
    output_json(envelope, ctx.no_meta)
