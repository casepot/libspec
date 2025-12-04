"""Shared utilities for lifecycle and navigation commands.

This module extracts common functionality used by both the lifecycle
command and the new navigation commands (next, blocked, gaps, progress).

Supports both:
- Maturity-based tracking (core maturity field)
- Legacy lifecycle_state tracking
"""

from typing import Any

from libspec.cli.models.lifecycle import (
    DevTransitionSpec,
    GateStatus,
    LifecycleEntity,
    MaturityGate,
    WorkflowSpec,
)

# Maturity level ordering for progression checks
MATURITY_ORDER = [
    "idea", "specified", "designed", "implemented",
    "tested", "documented", "released", "deprecated"
]

MATURITY_INDEX = {m: i for i, m in enumerate(MATURITY_ORDER)}


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


def get_entity_state(entity: LifecycleEntity) -> str | None:
    """Get state from entity, preferring maturity over lifecycle_state."""
    state = entity.get("maturity")
    if not state:
        state = entity.get("lifecycle_state")
    return state


def get_entity_evidence(entity: LifecycleEntity) -> list[dict[str, Any]]:
    """Get evidence from entity, preferring maturity_evidence over state_evidence."""
    evidence = entity.get("maturity_evidence", [])
    if not evidence:
        evidence = entity.get("state_evidence", [])
    return evidence


def get_next_maturity(current: str) -> str | None:
    """Get the next maturity level in progression."""
    if current not in MATURITY_INDEX:
        return None
    idx = MATURITY_INDEX[current]
    if idx < len(MATURITY_ORDER) - 1:
        return MATURITY_ORDER[idx + 1]
    return None


def get_maturity_gate(
    from_maturity: str,
    to_maturity: str,
    workflow: WorkflowSpec,
) -> MaturityGate | None:
    """Get the maturity gate for a transition if defined."""
    for gate in workflow.get("maturity_gates", []):
        if gate.get("from_maturity") == from_maturity and gate.get("to_maturity") == to_maturity:
            return gate
    return None


def get_valid_next_states(current_state: str, workflow: WorkflowSpec) -> list[str]:
    """Get valid next states from current state (legacy state-based)."""
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
    transition: DevTransitionSpec | MaturityGate,
) -> list[GateStatus]:
    """Check which gates are satisfied/unsatisfied for a transition.

    Works with both legacy DevTransitionSpec and new MaturityGate.
    """
    gates = transition.get("gates", [])
    evidence_list = get_entity_evidence(entity)

    # Build set of evidence types, including custom type names
    evidence_types: set[str] = set()
    for ev in evidence_list:
        ev_type = ev.get("type")
        if ev_type == "custom":
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
        evidence_type = type_mapping.get(gate_type, gate_type)
        satisfied = evidence_type in evidence_types
        results.append({
            "gate": gate_type,
            "required": gate.get("required", True),
            "satisfied": satisfied,
        })
    return results


def collect_entities_with_tracking(spec: dict[str, Any]) -> list[LifecycleEntity]:
    """Collect all entities that have maturity or lifecycle_state set.

    Supports both:
    - Maturity-based tracking (core maturity field)
    - Legacy lifecycle_state tracking
    """
    entities: list[LifecycleEntity] = []
    library = spec.get("library", {})

    # Types
    for t in library.get("types", []):
        if "maturity" in t or "lifecycle_state" in t:
            entities.append({
                "entity_type": "type",
                "name": t.get("name"),
                "ref": f"#/types/{t.get('name')}",
                "maturity": t.get("maturity"),
                "maturity_evidence": t.get("maturity_evidence", []),
                "lifecycle_state": t.get("lifecycle_state"),
                "workflow": t.get("workflow"),
                "state_evidence": t.get("state_evidence", []),
            })

    # Functions
    for f in library.get("functions", []):
        if "maturity" in f or "lifecycle_state" in f:
            entities.append({
                "entity_type": "function",
                "name": f.get("name"),
                "ref": f"#/functions/{f.get('name')}",
                "maturity": f.get("maturity"),
                "maturity_evidence": f.get("maturity_evidence", []),
                "lifecycle_state": f.get("lifecycle_state"),
                "workflow": f.get("workflow"),
                "state_evidence": f.get("state_evidence", []),
            })

    # Features
    for feat in library.get("features", []):
        if "maturity" in feat or "lifecycle_state" in feat:
            entities.append({
                "entity_type": "feature",
                "name": feat.get("id"),
                "ref": f"#/features/{feat.get('id')}",
                "maturity": feat.get("maturity"),
                "maturity_evidence": feat.get("maturity_evidence", []),
                "lifecycle_state": feat.get("lifecycle_state"),
                "workflow": feat.get("workflow"),
                "state_evidence": feat.get("state_evidence", []),
            })

    # Methods in types
    for t in library.get("types", []):
        for m in t.get("methods", []):
            if "maturity" in m or "lifecycle_state" in m:
                entities.append({
                    "entity_type": "method",
                    "name": f"{t.get('name')}.{m.get('name')}",
                    "ref": f"#/types/{t.get('name')}/methods/{m.get('name')}",
                    "maturity": m.get("maturity"),
                    "maturity_evidence": m.get("maturity_evidence", []),
                    "lifecycle_state": m.get("lifecycle_state"),
                    "workflow": m.get("workflow"),
                    "state_evidence": m.get("state_evidence", []),
                })

    return entities


def check_requirement_satisfied(
    req: dict[str, Any],
    entity_maturities: dict[str, str | None],
) -> tuple[bool, str | None]:
    """Check if a requirement is satisfied.

    Args:
        req: Requirement dict with 'ref' and optional 'min_maturity'
        entity_maturities: Map of entity refs to their maturity levels

    Returns:
        Tuple of (is_satisfied, reason if not satisfied)
    """
    ref = req.get("ref")
    min_maturity = req.get("min_maturity")

    if not ref:
        return True, None

    actual = entity_maturities.get(ref)

    # If ref doesn't exist, that's a different issue (X001)
    if actual is None:
        return True, None

    # If no min_maturity specified, just check existence
    if not min_maturity:
        return True, None

    # Check maturity level
    actual_idx = MATURITY_INDEX.get(actual, -1)
    min_idx = MATURITY_INDEX.get(min_maturity, 0)

    if actual_idx < min_idx:
        return False, f"requires '{ref}' at '{min_maturity}' (currently: '{actual}')"

    return True, None


def collect_entity_maturities(spec: dict[str, Any]) -> dict[str, str | None]:
    """Collect maturity levels for all entities.

    Returns:
        Dict mapping entity refs to their maturity level.
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
