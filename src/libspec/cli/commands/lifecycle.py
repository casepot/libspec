"""Lifecycle commands: lifecycle report and analysis."""

from collections import defaultdict
from typing import Any

import click

from libspec.cli.app import Context, pass_context
from libspec.cli.models.lifecycle import (
    BlockedItem,
    DevTransitionSpec,
    GateStatus,
    LifecycleEntity,
    WorkflowSpec,
)
from libspec.cli.output import make_envelope, output_json


def get_entity_workflow(entity: LifecycleEntity, spec: dict[str, Any]) -> str | None:
    """Get the workflow for an entity (explicit or default)."""
    if workflow := entity.get("workflow"):
        return workflow
    default: str | None = spec.get("library", {}).get("default_workflow")
    return default


def get_workflow_spec(workflow_name: str, spec: dict[str, Any]) -> WorkflowSpec | None:
    """Get a workflow specification by name."""
    workflows: list[WorkflowSpec] = spec.get("library", {}).get("workflows", [])
    for w in workflows:
        if w.get("name") == workflow_name:
            return w
    return None


def get_valid_next_states(current_state: str, workflow: WorkflowSpec) -> list[str]:
    """Get valid next states from current state."""
    transitions = workflow.get("transitions", [])
    next_states: list[str] = []
    for t in transitions:
        if t.get("from_state") == current_state:
            to_state = t.get("to_state")
            if to_state:
                next_states.append(to_state)
    return next_states


def check_gates_satisfied(
    entity: LifecycleEntity,
    transition: DevTransitionSpec,
) -> list[GateStatus]:
    """Check which gates are satisfied/unsatisfied for a transition."""
    gates = transition.get("gates", [])
    evidence_list = entity.get("state_evidence", [])

    # Build set of evidence types, including custom type names
    evidence_types: set[str] = set()
    for ev in evidence_list:
        ev_type = ev.get("type")
        if ev_type == "custom":
            # For custom evidence, use the type_name
            # Cast needed because TypedDict union doesn't narrow on discriminator
            type_name: str | None = ev.get("type_name")  # type: ignore[assignment]
            if type_name:
                evidence_types.add(type_name)
        elif ev_type:
            evidence_types.add(ev_type)

    # Map gate types to evidence types
    type_mapping = {
        "design_doc": "design_doc",
        "pr_merged": "pr",
        "tests_passing": "tests",
        "docs_updated": "docs",
        "approval": "approval",
        "benchmark": "benchmark",
        "migration_guide": "migration_guide",
        "deprecation_notice": "deprecation_notice",
    }

    results: list[GateStatus] = []
    for gate in gates:
        gate_type = gate.get("type", "")
        # Map to evidence type, or use gate_type directly for custom gates
        evidence_type = type_mapping.get(gate_type, gate_type)
        satisfied = evidence_type in evidence_types
        results.append({
            "gate": gate_type,
            "required": gate.get("required", True),
            "satisfied": satisfied,
        })
    return results


def collect_entities_with_lifecycle(spec: dict[str, Any]) -> list[LifecycleEntity]:
    """Collect all entities that have lifecycle_state set."""
    entities: list[LifecycleEntity] = []
    library = spec.get("library", {})

    # Types
    for t in library.get("types", []):
        if "lifecycle_state" in t:
            entities.append({
                "entity_type": "type",
                "name": t.get("name"),
                "ref": f"#/types/{t.get('name')}",
                "lifecycle_state": t.get("lifecycle_state"),
                "workflow": t.get("workflow"),
                "state_evidence": t.get("state_evidence", []),
            })

    # Functions
    for f in library.get("functions", []):
        if "lifecycle_state" in f:
            entities.append({
                "entity_type": "function",
                "name": f.get("name"),
                "ref": f"#/functions/{f.get('name')}",
                "lifecycle_state": f.get("lifecycle_state"),
                "workflow": f.get("workflow"),
                "state_evidence": f.get("state_evidence", []),
            })

    # Features
    for feat in library.get("features", []):
        if "lifecycle_state" in feat:
            entities.append({
                "entity_type": "feature",
                "name": feat.get("id"),
                "ref": f"#/features/{feat.get('id')}",
                "lifecycle_state": feat.get("lifecycle_state"),
                "workflow": feat.get("workflow"),
                "state_evidence": feat.get("state_evidence", []),
            })

    # Methods in types
    for t in library.get("types", []):
        for m in t.get("methods", []):
            if "lifecycle_state" in m:
                entities.append({
                    "entity_type": "method",
                    "name": f"{t.get('name')}.{m.get('name')}",
                    "ref": f"#/types/{t.get('name')}/methods/{m.get('name')}",
                    "lifecycle_state": m.get("lifecycle_state"),
                    "workflow": m.get("workflow"),
                    "state_evidence": m.get("state_evidence", []),
                })

    return entities


@click.command()
@click.option("--workflow", "-w", help="Filter by workflow name")
@click.option("--state", "-s", help="Filter by lifecycle state")
@click.option(
    "--blocked",
    is_flag=True,
    help="Show only blocked entities (missing required gates)",
)
@click.option("--summary", is_flag=True, help="Show summary statistics only")
@pass_context
def lifecycle(
    ctx: Context,
    workflow: str | None,
    state: str | None,
    blocked: bool,
    summary: bool,
) -> None:
    """
    Analyze entity lifecycle states and transitions.

    \b
    Reports:
      - Counts by state across all workflows
      - Blocked items missing required gates
      - Invalid transitions detected

    \b
    Examples:
        libspec lifecycle                    # Full report
        libspec lifecycle --summary          # Just counts
        libspec lifecycle --blocked          # Show blocked items
        libspec lifecycle --state implemented
        libspec lifecycle --workflow standard
    """
    spec = ctx.get_spec()

    # Check if lifecycle extension is enabled
    if "lifecycle" not in spec.extensions:
        raise click.ClickException(
            "Lifecycle extension not enabled. Add 'lifecycle' to extensions array."
        )

    entities = collect_entities_with_lifecycle(spec.data)
    workflows_def = spec.workflows
    default_workflow = spec.default_workflow

    # Apply filters
    if workflow:
        entities = [
            e for e in entities
            if (e.get("workflow") or default_workflow) == workflow
        ]
    if state:
        entities = [e for e in entities if e.get("lifecycle_state") == state]

    # Compute statistics
    by_state: dict[str, int] = defaultdict(int)
    by_workflow: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    by_entity_type: dict[str, int] = defaultdict(int)
    blocked_items: list[BlockedItem] = []

    for entity in entities:
        entity_state = entity.get("lifecycle_state", "unknown")
        entity_workflow = entity.get("workflow") or default_workflow
        entity_type = entity.get("entity_type")

        by_state[entity_state] += 1
        if entity_workflow:
            by_workflow[entity_workflow][entity_state] += 1
        if entity_type:
            by_entity_type[entity_type] += 1

        # Check for blocked items
        if entity_workflow:
            wf = get_workflow_spec(entity_workflow, spec.data)
            if wf:
                next_states = get_valid_next_states(entity_state, wf)
                for next_state in next_states:
                    # Find the transition
                    for t in wf.get("transitions", []):
                        if (
                            t.get("from_state") == entity_state
                            and t.get("to_state") == next_state
                        ):
                            gate_status = check_gates_satisfied(entity, t)
                            unsatisfied = [
                                g for g in gate_status
                                if g["required"] and not g["satisfied"]
                            ]
                            if unsatisfied:
                                blocked_items.append({
                                    "entity": entity["ref"],
                                    "name": entity["name"],
                                    "current_state": entity_state,
                                    "blocked_transition": next_state,
                                    "unsatisfied_gates": [
                                        g["gate"] for g in unsatisfied
                                    ],
                                })

    # Build result
    result: dict[str, Any] = {
        "total_tracked": len(entities),
        "by_state": dict(by_state),
        "by_entity_type": dict(by_entity_type),
    }

    if not summary:
        result["by_workflow"] = {k: dict(v) for k, v in by_workflow.items()}
        result["blocked"] = blocked_items

        if not blocked:
            result["entities"] = entities

    if blocked:
        blocked_refs = {b["entity"] for b in blocked_items}
        result["entities"] = [e for e in entities if e["ref"] in blocked_refs]

    if ctx.text:
        click.echo(f"Lifecycle tracked: {len(entities)} entities")
        click.echo("")
        click.echo("By state:")
        for state_name, count in sorted(by_state.items()):
            click.echo(f"  {state_name}: {count}")
        click.echo("")
        if blocked_items:
            click.echo(f"Blocked: {len(blocked_items)} items")
            for item in blocked_items[:5]:  # Show first 5
                gates = ", ".join(item["unsatisfied_gates"])
                click.echo(f"  {item['name']}: needs {gates}")
            if len(blocked_items) > 5:
                click.echo(f"  ... and {len(blocked_items) - 5} more")
        click.echo("---")
        click.echo(f"{len(entities)} entities, {len(blocked_items)} blocked")
        return

    envelope = make_envelope(
        "lifecycle",
        spec,
        result,
        meta={
            "total": len(entities),
            "blocked_count": len(blocked_items),
            "workflows": [w.get("name") for w in workflows_def],
        },
    )
    output_json(envelope, ctx.no_meta)
