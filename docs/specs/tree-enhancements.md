# Tree Enhancements Feature Spec

## Overview

This document specifies enhancements to `libspec modules --tree` for richer codebase visualization.

---

## 1. `--entities` Flag

**Purpose:** Show types and functions nested under their respective modules.

### Basic Usage

```bash
$ libspec modules --tree --entities
mylib/
├── core/
│   ├── class Handler
│   ├── class Response
│   ├── protocol Serializable
│   └── func parse_config
└── client/
    ├── class Client
    └── func connect
```

### With `--internal`

```bash
$ libspec modules --tree --entities --internal
mylib/
├── core/
│   ├── class Handler
│   ├── class Response
│   └── _utils/ (internal)
│       └── func _parse_impl
└── client/
    └── class Client
```

### Entity Display Format

Each entity shows its kind prefix:
- `class` - Regular class
- `dataclass` - Dataclass
- `protocol` - Protocol
- `enum` - Enum
- `alias` - Type alias
- `func` - Function
- `decorator` - Decorator
- `ctxmgr` - Context manager

### JSON Structure

```json
{
  "result": {
    "name": "mylib",
    "path": "mylib",
    "entities": [
      {"name": "Client", "kind": "class", "entity_type": "type"},
      {"name": "connect", "kind": "function", "entity_type": "function"}
    ],
    "children": [...]
  }
}
```

### Implementation Notes

- Entities are matched to modules by their `module` field
- Entities sort: types first (alphabetically), then functions (alphabetically)
- Internal types/functions follow module visibility (if module is internal, so are its entities)

---

## 2. `--depth` Flag

**Purpose:** Limit tree traversal depth for large codebases.

### Usage

```bash
$ libspec modules --tree --depth 1
mylib/
├── core/
├── client/
└── utils/
```

```bash
$ libspec modules --tree --depth 2
mylib/
├── core/
│   ├── handlers/
│   └── models/
├── client/
│   └── http/
└── utils/
```

### With `--entities`

When `--entities` is used, depth applies to modules only. Entities at visible modules are always shown:

```bash
$ libspec modules --tree --entities --depth 1
mylib/
├── class Client
├── func connect
├── core/
└── client/
```

---

## 3. Entity Filters

**Purpose:** Filter which entity types appear in `--entities` output.

### `--types-only`

Show only type definitions (classes, protocols, enums, etc.):

```bash
$ libspec modules --tree --entities --types-only
mylib/
├── core/
│   ├── class Handler
│   └── protocol Serializable
└── client/
    └── class Client
```

### `--functions-only`

Show only function definitions:

```bash
$ libspec modules --tree --entities --functions-only
mylib/
├── core/
│   └── func parse_config
└── client/
    └── func connect
```

### `--kind`

Filter by specific kind:

```bash
$ libspec modules --tree --entities --kind protocol
mylib/
└── core/
    └── protocol Serializable

$ libspec modules --tree --entities --kind decorator
mylib/
└── utils/
    └── decorator cached
```

---

## 4. `--methods` Flag

**Purpose:** Expand types to show their methods (deeper drill-down).

### Usage

```bash
$ libspec modules --tree --entities --methods
mylib/
└── core/
    └── class Handler
        ├── def handle(self, request) -> Response
        ├── def validate(self, data) -> bool
        └── async def process(self) -> None
```

### Considerations

- This creates deep nesting; consider combining with `--depth`
- Method signatures are shown in compact form
- Properties could be included with `--properties` or combined via `--members`

---

## 5. `--compact` Flag

**Purpose:** Reduce visual noise for large trees.

### Usage

```bash
$ libspec modules --tree --compact
mylib/
  core/ [3 types, 2 funcs]
  client/ [1 type, 1 func]
  utils/ (internal) [2 funcs]
```

### With `--entities`

Entities shown inline when few, expanded when many:

```bash
$ libspec modules --tree --entities --compact
mylib/
  core/ Handler, Response, Serializable, parse_config, validate
  client/ Client, connect
```

---

## 6. `--stats` Flag

**Purpose:** Show statistics instead of/alongside entities.

### Usage

```bash
$ libspec modules --tree --stats
mylib/                      [5 types, 3 funcs, 2 deps]
├── core/                   [3 types, 1 func, 0 deps]
└── client/                 [2 types, 2 funcs, 1 dep]
```

---

## Priority

| Feature | Priority | Complexity | Notes |
|---------|----------|------------|-------|
| `--entities` | High | Medium | Core feature, enables module-entity view |
| `--depth` | Medium | Low | Simple counter during traversal |
| `--types-only` / `--functions-only` | Medium | Low | Filter on entity_type |
| `--kind` | Low | Low | Filter on kind field |
| `--methods` | Low | High | Requires restructuring tree nodes |
| `--compact` | Low | Medium | Alternative rendering mode |
| `--stats` | Low | Low | Aggregate counts |

---

## Implementation Order

1. **`--entities`** - Foundation for entity-aware tree
2. **`--depth`** - Essential for large codebases
3. **Entity filters** (`--types-only`, `--functions-only`) - Quick wins
4. **`--stats`** - Useful summary view
5. **`--compact`** - Nice-to-have
6. **`--methods`** - Advanced feature, defer

---

## Model Changes

### ModuleEntity (new)

```python
class ModuleEntity(BaseModel):
    name: str
    kind: str  # "class", "protocol", "function", etc.
    entity_type: str  # "type" or "function"
```

### ModuleTreeNode (updated)

```python
class ModuleTreeNode(BaseModel):
    name: str
    path: str
    exports: list[str] = []
    depends_on: list[str] = []
    internal: bool = False
    is_package: bool = True
    entities: list[ModuleEntity] = []  # NEW
    children: list[ModuleTreeNode] = []
```

### build_module_tree (updated signature)

```python
def build_module_tree(
    modules: list[Module],
    types: list[TypeDef] | None = None,      # NEW
    functions: list[FunctionDef] | None = None,  # NEW
    include_internal: bool = False,
) -> ModuleTreeNode | None:
```

---

## CLI Changes

```python
@click.command()
@click.option("--tree", is_flag=True)
@click.option("--internal", is_flag=True)
@click.option("--exports", is_flag=True)
@click.option("--deps", is_flag=True)
@click.option("--entities", is_flag=True, help="Show types/functions under modules")
@click.option("--depth", type=int, help="Limit tree depth")
@click.option("--types-only", is_flag=True, help="Only show types (with --entities)")
@click.option("--functions-only", is_flag=True, help="Only show functions (with --entities)")
@click.option("--format", type=click.Choice(["text", "json", "dot", "mermaid"]))
def modules(...):
```
