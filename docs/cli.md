# CLI Reference

The `libspec` command-line tool queries, validates, and analyzes library specifications.

## Installation

```bash
pip install libspec[cli]
```

Requires Python 3.10+ and optionally `jq` for the `query` command.

## Quick Start

```bash
# Overview of your spec
libspec info

# List all types
libspec types

# Run jq queries
libspec query '.library.types[] | select(.kind=="protocol")'

# Validate and lint
libspec validate && libspec lint --strict
```

## Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--spec PATH` | `-s` | Path to libspec.json (auto-detected if omitted) |
| `--text` | `-t` | Token-minimal text output instead of JSON |
| `--no-meta` | | Omit metadata envelope from JSON output |
| `--config PATH` | `-c` | Path to pyproject.toml |
| `--version` | | Show version |
| `--help` | | Show help |

### Spec Auto-Detection

If `--spec` is not provided, libspec looks for:
1. `spec_path` in `[tool.libspec]` config
2. `libspec.json` in current directory
3. `specs/libspec.json`
4. `spec/libspec.json`

---

## Output Formats

### JSON (default)

All commands output a consistent JSON envelope:

```json
{
  "libspec_cli": "0.1.0",
  "command": "types",
  "spec": {
    "path": "specs/libspec.json",
    "library": "mylib",
    "version": "0.1.0"
  },
  "timestamp": "2025-12-01T12:00:00Z",
  "result": [...],
  "meta": {"count": 12}
}
```

Pipe to `jq` for extraction:
```bash
libspec types | jq '.result[].name'
libspec info | jq '.result.counts'
```

### Text (`--text`)

Token-minimal output, one entity per line:

```
$ libspec types --text
TYPE class Connection mylib.client
TYPE protocol Handler mylib.handlers
TYPE enum Status mylib.types
---
3 types
```

---

## Commands

### Inspect Commands

#### `libspec info`

Show spec overview: library info, entity counts, extensions, coverage.

```bash
libspec info                    # Full overview
libspec info --counts-only      # Just counts
libspec info -t                 # Text format
```

#### `libspec types`

List type definitions (classes, protocols, enums, dataclasses).

```bash
libspec types                       # All types
libspec types --kind protocol       # Only protocols
libspec types --kind enum           # Only enums
libspec types -m 'mylib\.core'      # Filter by module (regex)
libspec types --undocumented        # Missing docstrings
libspec types --lifecycle-state implemented  # Filter by lifecycle
```

#### `libspec functions`

List function definitions.

```bash
libspec functions                   # All functions
libspec functions --kind decorator  # Only decorators
libspec functions --lifecycle-state tested  # Filter by lifecycle
```

#### `libspec features`

List behavioral specifications.

```bash
libspec features                    # All features
libspec features --status planned   # Not yet implemented
libspec features --status tested    # With test coverage
libspec features -c CONNECTION      # Filter by category
libspec features --lifecycle-state released  # Filter by lifecycle
```

#### `libspec modules`

List module definitions and dependencies.

```bash
libspec modules                     # Public modules
libspec modules --internal          # Include internal
```

#### `libspec principles`

List design principles.

```bash
libspec principles
libspec principles --with-implications
```

---

### Query Commands

#### `libspec query EXPRESSION`

Run a jq expression against the spec. Requires `jq` installed.

```bash
# Basic queries
libspec query '.library.types[].name'
libspec query '.library.types | length'

# Filtering
libspec query '.library.types[] | select(.kind=="protocol")'
libspec query '.library.features[] | select(.status=="planned")'

# Shortcuts (expand to jq expressions)
libspec query type-names        # → .library.types[].name
libspec query function-names    # → .library.functions[].name
libspec query feature-ids       # → .library.features[].id

# Output options
libspec query type-names -r     # Raw output (no quotes)
libspec query type-names -c     # Compact (one line)
```

#### `libspec refs REFERENCE`

Resolve a cross-reference to its full definition.

```bash
libspec refs '#/types/Connection'
libspec refs '#/types/Connection/methods/send'
libspec refs '#/functions/spawn'
libspec refs '#/features/connection-retry'
```

#### `libspec search PATTERN`

Search for a regex pattern across names and descriptions.

```bash
libspec search connection
libspec search 'async.*handler' --type types
libspec search retry --in descriptions
```

---

### Validate Commands

#### `libspec validate`

Validate spec against JSON Schema.

```bash
libspec validate
libspec validate --strict       # Exit code 3 on failure
```

#### `libspec lint`

Run semantic linting with configurable rules.

```bash
libspec lint                    # All rules
libspec lint --strict           # Exit code 4 on issues
libspec lint -r S001 -r S002    # Specific rules only
libspec lint --severity error   # Only errors
libspec lint --list-rules       # Show available rules
```

---

### Analyze Commands

#### `libspec coverage`

Analyze feature and documentation coverage.

```bash
libspec coverage
libspec coverage --type features    # Feature status only
libspec coverage --type docs        # Documentation only
```

Output includes:
- Feature counts by status (planned/implemented/tested)
- Documentation coverage percentages
- List of gaps (undocumented, untested)

#### `libspec deps`

Analyze type and module dependencies.

```bash
libspec deps                            # Full graph
libspec deps --type Connection          # What Connection uses
libspec deps --type Connection --reverse  # What uses Connection
libspec deps --format dot               # Graphviz DOT output
libspec deps --format mermaid           # Mermaid diagram
```

#### `libspec surface`

Analyze public API surface area.

```bash
libspec surface
libspec surface --public-only   # Exclude internal modules
libspec surface --by-module     # Breakdown per module
```

---

### Lifecycle Commands

#### `libspec lifecycle`

Analyze entity lifecycle states and transitions. Requires the `lifecycle` extension.

```bash
libspec lifecycle                    # Full report
libspec lifecycle --summary          # Just counts
libspec lifecycle --blocked          # Show blocked items
libspec lifecycle --state implemented
libspec lifecycle --workflow standard
```

| Option | Description |
|--------|-------------|
| `-w, --workflow TEXT` | Filter by workflow name |
| `-s, --state TEXT` | Filter by lifecycle state |
| `--blocked` | Show only blocked entities (missing required gates) |
| `--summary` | Show summary statistics only |

Output includes:
- Counts by state across all workflows
- Blocked items missing required gates
- Entity breakdown by type

See [Lifecycle Extension](lifecycle.md) for full documentation.

---

## Lint Rules

Rules are organized by category:

| Category | Prefix | Focus |
|----------|--------|-------|
| Structural | `S` | Missing descriptions, empty types |
| Naming | `N` | Kebab-case IDs, PascalCase types |
| Completeness | `C` | Features without steps, missing signatures |
| Consistency | `X` | Dangling refs, duplicates |
| Lifecycle | `L` | Lifecycle states, transitions, evidence |

### Available Rules

| Rule | Severity | Description |
|------|----------|-------------|
| S001 | error | Type missing docstring |
| S002 | warning | Method missing description |
| S003 | warning | Function missing description |
| S007 | warning | Type has no methods or properties |
| N001 | warning | Feature ID should be kebab-case |
| N002 | warning | Principle ID should be kebab-case |
| N003 | warning | Type name should be PascalCase |
| N004 | warning | Function name should be snake_case |
| N006 | warning | Feature category should be SCREAMING_SNAKE |
| C001 | warning | Feature has no verification steps |
| C002 | error | Method missing signature |
| C003 | error | Type missing module path |
| C005 | warning | Enum has no values |
| C006 | warning | Protocol has no methods |
| C007 | info | Feature has no cross-references |
| X001 | error | Dangling cross-reference |
| X002 | error | Duplicate type name |
| X003 | error | Duplicate feature ID |
| X006 | warning | Feature marked tested but has no steps |
| L001 | error | Invalid lifecycle state (not in workflow) |
| L002 | warning | Missing required evidence for lifecycle state |
| L003 | error | Dangling workflow reference |
| L004 | info | Lifecycle/feature status mismatch |
| L005 | error | Invalid workflow definition |
| L006 | warning | Evidence reference format invalid for type |
| L007 | error | Custom evidence references undefined type |
| L008 | warning | Evidence missing required field for type |
| L009 | info | Test evidence path doesn't look like a test file |

### Configuration

Configure lint rules in `pyproject.toml`:

```toml
[tool.libspec]
spec_path = "specs/libspec.json"

[tool.libspec.lint]
enable = ["all"]
disable = ["C007"]          # Ignore missing refs warning

[tool.libspec.lint.rules]
S001 = "warning"            # Downgrade to warning
N001 = "info"               # Downgrade naming violations
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error (invalid arguments, etc.) |
| 2 | Spec file not found |
| 3 | Schema validation failed (with `--strict`) |
| 4 | Lint issues found (with `--strict`) |
| 5 | jq not installed |

---

## Workflows

### CI Validation

```bash
#!/bin/bash
set -e
libspec validate --strict
libspec lint --strict --severity error
```

### Exploring a New Spec

```bash
# Start with overview
libspec info

# Drill into types
libspec types
libspec types --kind protocol

# Search for specific concepts
libspec search connection

# Check specific entity
libspec refs '#/types/Connection'

# Run jq for custom queries
libspec query '.library.types[] | {name, methods: [.methods[].name]}'
```

### Finding Documentation Gaps

```bash
# Undocumented types
libspec types --undocumented

# Coverage analysis
libspec coverage --type docs

# Lint for missing descriptions
libspec lint -r S001 -r S002 -r S003
```

---

## Limitations

**Current limitations:**

- `modules --tree` flag is accepted but ignored; output is always a flat list.
- `coverage --threshold` is parsed but unused; coverage never fails based on the value.
- Extension schema merging during validation is TODO, so extension fields are not validated against their schemas.
- No lint auto-fix path: there is no `--fix` flag and no rules invoke `fix()`, so issues are only reported.
- External cross-reference validation is skipped (e.g., `other_lib#/types/X` are not checked for existence).

**jq dependency:**

The `query` command requires jq to be installed separately:
- macOS: `brew install jq`
- Ubuntu: `apt install jq`
- Windows: `choco install jq`

---

## Future Enhancements

**High value:**
- `libspec diff` – Compare two spec versions and surface API changes (no stub exists yet)
- `libspec generate` – Emit Python stubs from a spec (no command registered)
- `libspec watch` – Continuous validation while editing (not started)
- Auto-fix for simple lint issues (e.g., kebab-case conversion); requires wiring a `--fix` mode and rule-level fixers

**Analysis:**
- Complexity metrics per type/module (no metrics calculated today)
- Breaking change detection between versions (diff logic not present)
- Test coverage mapping linking features to real test files (only counts statuses now)

**Integration:**
- Pre-commit hook support (no hook config shipped)
- GitHub Actions integration (no workflow templates in repo)
- VS Code extension for inline validation (no extension code or manifest yet)
