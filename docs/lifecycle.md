# Lifecycle Extension

The `lifecycle` extension adds workflow orchestration on top of libspec's core maturity tracking. It enables gate criteria, evidence tracking, and formal workflow definitions.

## Architecture

Libspec uses a layered approach to development tracking:

```
+-----------------------------------------------------+
|  Lifecycle Extension (Optional Layer)               |
|  -------------------------------------------        |
|  - Workflows define HOW to progress through maturity|
|  - Gates: evidence/approval required per transition |
|  - Evidence tracking for auditing/compliance        |
|  - Answers: "Can this entity advance?"              |
+-----------------------------------------------------+
|  Core: maturity field (Always Available)            |
|  -------------------------------------------        |
|  - Universal "WHERE is this in development"         |
|  - Fixed enum progression                           |
|  - No extension needed                              |
|  - Answers: "How developed is this?"                |
+-----------------------------------------------------+
```

**Key insight**: `maturity` is the core field tracking development stage. The `lifecycle` extension adds workflow orchestration (gates, evidence) around maturity transitions.

---

## Core Maturity Field

Every entity (type, function, feature, method) can have a `maturity` field tracking its development stage. This is a **core field** - no extension required.

### Maturity Levels

| Level | Description |
|-------|-------------|
| `idea` | Rough concept, may change significantly |
| `specified` | Behavior described, acceptance criteria clear |
| `designed` | Shape defined (signatures, contracts, types) |
| `implemented` | Code exists |
| `tested` | Tests exist and pass |
| `documented` | User-facing docs exist |
| `released` | Part of a public release |
| `deprecated` | Marked for removal |

### Usage Without Lifecycle Extension

```json
{
  "$schema": "libspec/1.0",
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "types": [
      {
        "name": "Connection",
        "kind": "class",
        "maturity": "designed",
        "docstring": "Manages network connections"
      },
      {
        "name": "MessageCodec",
        "kind": "protocol",
        "maturity": "implemented",
        "docstring": "Protocol for encoding/decoding messages"
      }
    ]
  }
}
```

### Dependency Tracking with `requires`

Entities can declare dependencies on other entities with optional maturity requirements:

```json
{
  "name": "WebSocketHandler",
  "kind": "class",
  "maturity": "specified",
  "requires": [
    {"ref": "#/types/Connection", "min_maturity": "designed"},
    {"ref": "#/types/MessageCodec", "min_maturity": "implemented"}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `ref` | string | Reference to required entity (`#/types/X`, `#/functions/Y`) |
| `min_maturity` | string | Minimum maturity level required (optional) |
| `reason` | string | Why this requirement exists (optional) |

---

## Lifecycle Extension

Enable the lifecycle extension to add workflow orchestration:

```json
{
  "$schema": "libspec/1.0",
  "extensions": ["lifecycle"],
  "library": {
    "name": "mylib",
    "version": "0.1.0",
    "default_workflow": "standard",
    "workflows": [...]
  }
}
```

### Maturity-Based Workflows (Recommended)

Define gates for transitions between maturity levels:

```json
{
  "workflows": [{
    "name": "standard",
    "description": "Standard API lifecycle workflow",
    "maturity_gates": [
      {
        "from_maturity": "specified",
        "to_maturity": "designed",
        "gates": [{"type": "design_doc", "required": true}]
      },
      {
        "from_maturity": "designed",
        "to_maturity": "implemented",
        "gates": [{"type": "pr_merged", "required": true}]
      },
      {
        "from_maturity": "implemented",
        "to_maturity": "tested",
        "gates": [{"type": "tests_passing", "required": true}]
      },
      {
        "from_maturity": "tested",
        "to_maturity": "documented",
        "gates": [{"type": "docs_updated", "required": true}]
      },
      {
        "from_maturity": "documented",
        "to_maturity": "released",
        "gates": [{"type": "approval"}]
      },
      {
        "from_maturity": "released",
        "to_maturity": "deprecated",
        "gates": [{"type": "deprecation_notice", "required": true}]
      }
    ],
    "evidence_types": []
  }]
}
```

#### MaturityGate Definition

| Field | Type | Description |
|-------|------|-------------|
| `from_maturity` | string | Source maturity level |
| `to_maturity` | string | Target maturity level |
| `gates` | array | Gate criteria that must be satisfied |
| `description` | string | What this transition represents |

### Entity Fields with Lifecycle

```json
{
  "name": "DataProcessor",
  "kind": "class",
  "maturity": "tested",
  "workflow": "standard",
  "maturity_evidence": [
    {"type": "design_doc", "reference": "docs/design/data-processor.md", "date": "2024-01-15"},
    {"type": "pr", "url": "https://github.com/org/repo/pull/42"},
    {"type": "tests", "path": "tests/test_data_processor.py"}
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `maturity` | string | Current maturity level (core field) |
| `workflow` | string | Workflow name (defaults to `default_workflow`) |
| `maturity_evidence` | array | Evidence supporting current maturity |

### Gate Types

Gates represent evidence required to transition between maturity levels:

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

### Evidence Types

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

### Custom Evidence Types

Workflows can define custom evidence types:

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

### Legacy State-Based Workflows

For backward compatibility, state-based workflows are still supported:

```json
{
  "workflows": [{
    "name": "legacy",
    "initial_state": "idea",
    "states": [
      {"name": "idea", "order": 0},
      {"name": "drafted", "order": 1},
      {"name": "implemented", "order": 2}
    ],
    "transitions": [
      {"from_state": "idea", "to_state": "drafted", "gates": [{"type": "design_doc"}]},
      {"from_state": "drafted", "to_state": "implemented", "gates": [{"type": "pr_merged"}]}
    ]
  }]
}
```

Use `lifecycle_state` and `state_evidence` fields with legacy workflows:

```json
{
  "name": "LegacyType",
  "kind": "class",
  "lifecycle_state": "drafted",
  "state_evidence": [...]
}
```

**Note**: Maturity-based workflows are recommended for new specs.

---

## CLI Commands

### Navigation Commands

Top-level commands for development workflow:

#### `libspec next`

Show entities ready to advance to next maturity level.

```bash
libspec next                      # All ready entities
libspec next -t type              # Only types
libspec next -m designed          # Currently at designed
libspec next --limit 5            # Top 5
```

**Options:**

| Option | Description |
|--------|-------------|
| `-t, --type TYPE` | Filter by entity type (type/function/feature/method/all) |
| `-m, --maturity LEVEL` | Filter by current maturity |
| `-w, --workflow NAME` | Filter by workflow (lifecycle mode) |
| `--module REGEX` | Filter by module (regex) |
| `--limit N` | Limit results |

**Output:**

```
NEXT feature user-auth (specified -> designed)
NEXT type Connection (designed -> implemented)
---
2 entities ready to advance
```

#### `libspec blocked`

Show entities blocked by unsatisfied gates or requirements.

```bash
libspec blocked                   # All blocked
libspec blocked -t feature        # Blocked features
libspec blocked --by-requirement  # Group by blocker
libspec blocked -g tests_passing  # Blocked by tests gate
```

**Options:**

| Option | Description |
|--------|-------------|
| `-t, --type TYPE` | Filter by entity type |
| `-m, --maturity LEVEL` | Filter by current maturity |
| `-g, --gate TYPE` | Filter by missing gate type |
| `--by-requirement` | Group by blocking requirement |
| `--limit N` | Limit results |

**Output:**

```
BLOCKED feature websocket-support (specified)
  - requires: Connection at 'designed' (currently: idea)
  - gate: design_doc not satisfied
---
1 entity blocked
```

#### `libspec navigate gaps`

Show entities missing expected information for their stage.

```bash
libspec navigate gaps             # All gaps
libspec navigate gaps -t type     # Type gaps only
libspec navigate gaps -i tests    # Missing tests
```

**Options:**

| Option | Description |
|--------|-------------|
| `-t, --type TYPE` | Filter by entity type |
| `-s, --state STATE` | Filter by lifecycle state |
| `-i, --issue TYPE` | Filter by gap type (signature/docstring/tests/evidence) |

#### `libspec navigate progress`

Show development progress summary.

```bash
libspec navigate progress         # Full progress
libspec navigate progress -t type # Types only
libspec navigate progress --format compact
```

**Options:**

| Option | Description |
|--------|-------------|
| `-w, --workflow NAME` | Filter by workflow |
| `-t, --type TYPE` | Filter by entity type |
| `--format FORMAT` | Output format (table/compact/json) |

**Output (compact):**

```
idea: 2 | specified: 3 | designed: 5 | implemented: 8 | tested: 6 | released: 4
---
28 tracked, 5 ready, 3 blocked
```

### `libspec lifecycle`

Full lifecycle analysis (requires lifecycle extension).

```bash
libspec lifecycle                 # Full report
libspec lifecycle --summary       # Just counts
libspec lifecycle --blocked       # Blocked items
libspec lifecycle --state tested  # Filter by state
```

**Options:**

| Option | Description |
|--------|-------------|
| `-w, --workflow NAME` | Filter by workflow |
| `-s, --state STATE` | Filter by maturity/lifecycle state |
| `--blocked` | Show only blocked entities |
| `--summary` | Show summary statistics only |

---

## Lint Rules

### Maturity Rules

| Rule | Severity | Description |
|------|----------|-------------|
| **M001** | warning | Feature maturity inconsistent with status field |

### Lifecycle Rules

| Rule | Severity | Description |
|------|----------|-------------|
| **L001** | error | Entity state not defined in workflow |
| **L002** | warning | Entity missing required evidence for state |
| **L003** | error | Entity references undefined workflow |
| **L004** | info | Feature lifecycle_state inconsistent with status |
| **L005** | error | Workflow has invalid state references |
| **L006** | warning | Evidence reference format invalid |
| **L007** | error | Custom evidence references undefined type |
| **L008** | warning | Evidence missing required field |
| **L009** | info | Test evidence path doesn't look like test file |

### Consistency Rules (requires tracking)

| Rule | Severity | Description |
|------|----------|-------------|
| **X004** | error | Circular dependency in requires chain |
| **X005** | warning | Required entity below min_maturity |

---

## Migration: lifecycle_state to maturity

If you have an existing spec using `lifecycle_state`, migrate to `maturity`:

### Before (Legacy)

```json
{
  "name": "MyType",
  "kind": "class",
  "lifecycle_state": "implemented",
  "state_evidence": [...]
}
```

### After (Recommended)

```json
{
  "name": "MyType",
  "kind": "class",
  "maturity": "implemented",
  "maturity_evidence": [...]
}
```

### State Mapping

Map legacy states to maturity levels:

| Legacy State | Maturity Level |
|--------------|----------------|
| `idea` | `idea` |
| `drafted`, `reviewed`, `approved` | `specified` or `designed` |
| `implemented` | `implemented` |
| `tested` | `tested` |
| `documented` | `documented` |
| `released`, `stable` | `released` |
| `deprecated` | `deprecated` |

Both field types are supported during migration. The CLI commands check `maturity` first, then fall back to `lifecycle_state`.

---

## Example Spec

See [docs/examples/lifecycle.json](examples/lifecycle.json) for a complete example.

---

## Use Cases

### Track API Maturity

```bash
# What's still being designed?
libspec types -t --maturity designed
libspec next -m specified

# What's ready for release?
libspec types -t --maturity documented

# What's deprecated?
libspec types -t --maturity deprecated
```

### Find Blocked Progress

```bash
# What needs work to advance?
libspec blocked

# What's blocking by missing gates?
libspec blocked -g tests_passing

# What's blocked by requirements?
libspec blocked --by-requirement
```

### Development Dashboard

```bash
# Quick progress summary
libspec navigate progress --format compact

# Full lifecycle report
libspec lifecycle --summary
```

### CI Integration

```bash
#!/bin/bash
set -e

# Validate references and workflow definitions
libspec lint -r X001 -r L003 -r L005 --strict

# Check for circular dependencies
libspec lint -r X004 --strict

# Warn about missing evidence (non-blocking)
libspec lint -r L002 -r M001

# Report progress
libspec navigate progress --format compact
```
