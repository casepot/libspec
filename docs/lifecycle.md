# Lifecycle Extension

The `lifecycle` extension tracks entity development maturity through defined workflows with states, transitions, gate criteria, and evidence tracking.

## Overview

APIs evolve through predictable stages: conception, design, implementation, testing, documentation, release, and eventually deprecation. The lifecycle extension makes this progression explicit and trackable.

**Key features:**
- Define custom workflows with named states
- Track transitions with required gates (evidence)
- Attach evidence (PRs, design docs, test files) to entities
- Query entities by lifecycle state
- Lint rules for validation

## Schema Structure

### Library-Level Fields

Enable the extension and define workflows:

```json
{
  "$schema": "libspec/1.0",
  "extensions": ["lifecycle"],
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "default_workflow": "standard",
    "workflows": [
      {
        "name": "standard",
        "description": "Standard API lifecycle",
        "initial_state": "idea",
        "states": [...],
        "transitions": [...],
        "allow_skip": false
      }
    ]
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `default_workflow` | string | Name of workflow applied to entities without explicit workflow |
| `workflows` | array | List of workflow definitions |

### Workflow Definition

```json
{
  "name": "standard",
  "description": "Standard API lifecycle workflow",
  "initial_state": "idea",
  "allow_skip": false,
  "states": [
    { "name": "idea", "order": 0, "description": "Initial concept" },
    { "name": "drafted", "order": 1, "required_evidence": ["design_doc"] },
    { "name": "reviewed", "order": 2 },
    { "name": "approved", "order": 3, "required_evidence": ["approval"] },
    { "name": "implemented", "order": 4, "required_evidence": ["pr"] },
    { "name": "tested", "order": 5, "required_evidence": ["tests"] },
    { "name": "documented", "order": 6, "required_evidence": ["docs"] },
    { "name": "released", "order": 7 },
    { "name": "deprecated", "order": 8, "terminal": true, "required_evidence": ["deprecation_notice"] },
    { "name": "removed", "order": 9, "terminal": true, "required_evidence": ["migration_guide"] }
  ],
  "transitions": [
    { "from_state": "idea", "to_state": "drafted", "gates": [{"type": "design_doc", "required": true}] },
    { "from_state": "drafted", "to_state": "reviewed" },
    { "from_state": "reviewed", "to_state": "approved", "gates": [{"type": "approval"}] },
    { "from_state": "approved", "to_state": "implemented", "gates": [{"type": "pr_merged"}] },
    { "from_state": "implemented", "to_state": "tested", "gates": [{"type": "tests_passing"}] },
    { "from_state": "tested", "to_state": "documented", "gates": [{"type": "docs_updated"}] },
    { "from_state": "documented", "to_state": "released" },
    { "from_state": "released", "to_state": "deprecated", "gates": [{"type": "deprecation_notice"}] },
    { "from_state": "deprecated", "to_state": "removed", "gates": [{"type": "migration_guide"}] }
  ]
}
```

#### State Definition

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | State identifier (kebab-case) |
| `description` | string | Human-readable description |
| `order` | integer | Position in progression (for reporting) |
| `terminal` | boolean | If true, no transitions out of this state |
| `required_evidence` | array | Evidence types required for this state |

#### Transition Definition

| Field | Type | Description |
|-------|------|-------------|
| `from_state` | string | Source state name |
| `to_state` | string | Target state name |
| `gates` | array | Gate criteria that must be satisfied |
| `description` | string | What this transition represents |

#### Gate Types

Gates represent evidence required to transition between states:

| Gate Type | Description |
|-----------|-------------|
| `design_doc` | Design document exists |
| `approval` | Approval from reviewer/lead |
| `pr_merged` | PR implementing the entity is merged |
| `tests_passing` | Tests for the entity pass |
| `docs_updated` | Documentation updated |
| `benchmark` | Performance benchmark results |
| `deprecation_notice` | Deprecation announced |
| `migration_guide` | Migration guide published |
| `custom` | Custom gate with validator |

### Entity-Level Fields

Lifecycle fields can be added to types, functions, features, and methods:

```json
{
  "name": "DataProcessor",
  "kind": "class",
  "module": "mylib.core",
  "docstring": "Processes data from various sources",
  "lifecycle_state": "tested",
  "workflow": "standard",
  "state_evidence": [
    { "type": "design_doc", "reference": "docs/design/data-processor.md", "date": "2024-01-15" },
    { "type": "approval", "reference": "https://github.com/org/repo/issues/10#issuecomment-123", "author": "lead-dev" },
    { "type": "pr", "url": "https://github.com/org/repo/pull/42" },
    { "type": "tests", "path": "tests/test_data_processor.py" }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `lifecycle_state` | string | Current state in the workflow |
| `workflow` | string | Optional workflow override (defaults to `default_workflow`) |
| `state_evidence` | array | Evidence supporting current state |

#### Evidence Types

Each evidence type has specific required fields:

| Type | Required Fields | Optional Fields | Description |
|------|-----------------|-----------------|-------------|
| `pr` | `url` | `description`, `date`, `author` | Pull/merge request link |
| `tests` | `path` | `description`, `date` | Path to test file/directory |
| `design_doc` | `reference` | `description`, `date`, `author` | Design document URL or path |
| `docs` | `url` | `description`, `date` | Documentation URL |
| `approval` | `reference`, `author` | `description`, `date` | Approval link with approver |
| `benchmark` | `reference` | `metrics`, `description`, `date` | Benchmark results |
| `migration_guide` | `reference` | `description`, `date` | Migration guide URL or path |
| `deprecation_notice` | `reference`, `date` | `description` | Deprecation announcement |
| `custom` | `type_name` | `reference`, `url`, `path`, `description`, `date`, `author` | Custom type defined in workflow |

**Example evidence entries:**

```json
{
  "state_evidence": [
    { "type": "pr", "url": "https://github.com/org/repo/pull/42", "date": "2024-01-20" },
    { "type": "tests", "path": "tests/test_processor.py" },
    { "type": "docs", "url": "https://docs.example.com/api/processor" },
    { "type": "approval", "reference": "https://github.com/org/repo/issues/10#issuecomment-123", "author": "tech-lead" }
  ]
}
```

#### Custom Evidence Types

Workflows can define custom evidence types with their own validation:

```json
{
  "workflows": [{
    "name": "enterprise",
    "evidence_types": [
      {
        "name": "security_review",
        "description": "Security team sign-off",
        "required_fields": ["reference", "author"],
        "reference_pattern": "^https://jira\\.company\\.com/browse/SEC-\\d+$"
      }
    ]
  }]
}
```

**EvidenceTypeSpec fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Type name (snake_case) |
| `description` | string | What this evidence represents |
| `required_fields` | array | Required fields: `reference`, `url`, `path`, `author`, `date` |
| `reference_pattern` | string | Regex pattern for validating `reference` field |
| `url_pattern` | string | Regex pattern for validating `url` field |

**Using custom evidence:**

```json
{
  "state_evidence": [
    {
      "type": "custom",
      "type_name": "security_review",
      "reference": "https://jira.company.com/browse/SEC-1234",
      "author": "security-team"
    }
  ]
}
```

---

## CLI Commands

### `libspec lifecycle`

Analyze entity lifecycle states and transitions.

```bash
libspec lifecycle                    # Full report
libspec lifecycle --summary          # Just counts
libspec lifecycle --blocked          # Show blocked items
libspec lifecycle --state implemented
libspec lifecycle --workflow standard
```

**Options:**

| Option | Description |
|--------|-------------|
| `-w, --workflow TEXT` | Filter by workflow name |
| `-s, --state TEXT` | Filter by lifecycle state |
| `--blocked` | Show only blocked entities (missing required gates) |
| `--summary` | Show summary statistics only |

**JSON Output:**

```json
{
  "total_tracked": 15,
  "by_state": {"idea": 2, "implemented": 5, "released": 8},
  "by_entity_type": {"type": 10, "function": 3, "feature": 2},
  "by_workflow": {"standard": {"idea": 2, "implemented": 5, "released": 8}},
  "blocked": [
    {
      "entity": "#/types/AsyncProcessor",
      "name": "AsyncProcessor",
      "current_state": "implemented",
      "blocked_transition": "tested",
      "unsatisfied_gates": ["tests_passing"]
    }
  ],
  "entities": [...]
}
```

**Text Output:**

```
Lifecycle tracked: 15 entities

By state:
  idea: 2
  implemented: 5
  released: 8

Blocked: 1 items
  AsyncProcessor: needs tests_passing
---
15 entities, 1 blocked
```

### `--lifecycle-state` Filter

Inspect commands support filtering by lifecycle state:

```bash
libspec types --lifecycle-state implemented
libspec functions --lifecycle-state tested
libspec features --lifecycle-state released
```

---

## Lint Rules

| Rule | Severity | Description |
|------|----------|-------------|
| **L001** | error | Entity has `lifecycle_state` not defined in its workflow |
| **L002** | warning | Entity missing required evidence for its lifecycle state |
| **L003** | error | Entity references undefined workflow |
| **L004** | info | Feature `lifecycle_state` inconsistent with `status` field |
| **L005** | error | Workflow has invalid initial_state or transition references |
| **L006** | warning | Evidence reference format invalid for its type |
| **L007** | error | Custom evidence references undefined type |
| **L008** | warning | Evidence missing required field for its type |
| **L009** | info | Test evidence path doesn't look like a test file |

### Rule Details

**L001 - Invalid Lifecycle State**

Triggers when an entity's `lifecycle_state` is not one of the states defined in its workflow.

```bash
# Find invalid states
libspec lint -r L001
```

**L002 - Missing Required Evidence**

Triggers when an entity is in a state that requires evidence (per `required_evidence` in the state definition) but the evidence is missing from `state_evidence`.

```bash
# Check evidence requirements
libspec lint -r L002
```

**L003 - Dangling Workflow Reference**

Triggers when an entity explicitly references a workflow that doesn't exist.

**L004 - Lifecycle/Feature Status Mismatch**

For features, checks that `lifecycle_state` is consistent with the `status` field:
- `idea`, `drafted`, `reviewed`, `approved` → `status: "planned"`
- `implemented` → `status: "implemented"`
- `tested`, `documented`, `released`, `deprecated`, `removed` → `status: "tested"`

**L005 - Invalid Workflow Definition**

Checks workflow internal consistency:
- `initial_state` must reference a defined state
- All transitions must reference valid `from_state` and `to_state`

**L006 - Invalid Evidence Reference**

Checks that evidence URLs are valid format:
- `pr` evidence must have valid URL format
- `docs` evidence must have valid URL format

```bash
# Check evidence URL formats
libspec lint -r L006
```

**L007 - Undefined Custom Evidence Type**

Triggers when custom evidence references a `type_name` not defined in the workflow's `evidence_types` array.

```bash
# Find undefined custom evidence types
libspec lint -r L007
```

**L008 - Evidence Missing Required Field**

Checks that evidence has all required fields for its type:
- `pr` requires `url`
- `tests` requires `path`
- `design_doc` requires `reference`
- `docs` requires `url`
- `approval` requires `reference` and `author`
- `benchmark` requires `reference`
- `migration_guide` requires `reference`
- `deprecation_notice` requires `reference` and `date`
- `custom` requires `type_name`

```bash
# Check evidence field requirements
libspec lint -r L008
```

**L009 - Invalid Test Path Pattern**

Checks that test evidence paths match common test file patterns:
- Contains `test` or `spec` in the path
- Follows common naming conventions (`*_test.py`, `*.spec.js`, etc.)
- Located in standard test directories (`tests/`, `__tests__/`)

```bash
# Check test path patterns
libspec lint -r L009
```

---

## Example Spec

See [docs/examples/lifecycle.json](examples/lifecycle.json) for a complete example with:
- Workflow definition with 10 states
- Types at different lifecycle stages
- Functions with lifecycle tracking
- Features linked to lifecycle states
- Evidence entries with references

---

## Use Cases

### Track API Maturity

```bash
# What's still in design?
libspec types --lifecycle-state drafted
libspec types --lifecycle-state idea

# What's ready for release?
libspec types --lifecycle-state documented

# What's deprecated?
libspec types --lifecycle-state deprecated
```

### Find Blocked Progress

```bash
# What needs work to advance?
libspec lifecycle --blocked

# What's blocking release?
libspec lifecycle --state documented --blocked
```

### Release Readiness

```bash
# Summary for release notes
libspec lifecycle --summary

# Check all entities have proper evidence
libspec lint -r L002 --strict
```

### CI Integration

```bash
#!/bin/bash
set -e

# Validate lifecycle states are valid
libspec lint -r L001 -r L003 -r L005 --strict

# Warn about missing evidence (non-blocking)
libspec lint -r L002

# Report lifecycle status
libspec lifecycle --summary -t
```
