# Extensions Reference

Extensions add domain-specific and cross-cutting semantics to your libspec specification. Enable extensions in the root of your spec file:

```json
{
  "$schema": "libspec/1.0",
  "extensions": ["async", "errors", "web"],
  "library": { ... }
}
```

## Extension Categories

### Domain Extensions

Extensions that model specific technical domains:

| Extension | Purpose |
|-----------|---------|
| [`async`](#async) | Async/concurrent semantics (lifecycle states, cancellation, scheduling) |
| [`cli`](#cli) | Command-line interface specifications |
| [`config`](#config) | Configuration management (sources, profiles, secrets) |
| [`data`](#data) | Data processing (dtypes, transforms, pipelines, I/O) |
| [`events`](#events) | Event-driven patterns (events, handlers, sagas) |
| [`orm`](#orm) | Object-relational mapping (models, relationships, migrations) |
| [`plugins`](#plugins) | Plugin systems (extension points, hooks, registries) |
| [`serialization`](#serialization) | Serialization patterns (formats, encoders, schemas) |
| [`state`](#state) | State management (Redux/MobX stores, XState machines) |
| [`testing`](#testing) | Test specifications (fixtures, mocks, factories) |
| [`web`](#web) | Web frameworks (routes, middleware, dependencies) |

### Concern Extensions

Extensions that address cross-cutting concerns:

| Extension | Purpose |
|-----------|---------|
| [`errors`](#errors) | Error handling (hierarchy, codes, recovery) |
| [`workflow`](#workflow) | Development workflow tracking (states, evidence, gates) |
| [`observability`](#observability) | Logging, metrics, tracing, health checks |
| [`perf`](#perf) | Performance characteristics (complexity, benchmarks) |
| [`safety`](#safety) | Thread safety, reentrancy, memory safety |
| [`versioning`](#versioning) | API versioning and deprecation |

---

## Domain Extensions

### async

**Purpose**: Model async/concurrent system semantics including lifecycle states, cancellation handling, synchronization primitives, and scheduling.

**Enable**: `"extensions": ["async"]`

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `lifecycle` | `LifecycleSpec` | State machine with states, transitions, triggers |
| `synchronization` | `SyncSpec` | Sync primitive specs (mailbox, channel, lock) |
| `observable` | `ObservableSpec` | Observable/stream specifications |
| `scheduling` | `SchedulingSpec` | Execution scheduling (executor, priority) |

#### Method/Function Fields

| Field | Type | Description |
|-------|------|-------------|
| `async` | `bool` | Whether async method/function |
| `awaitable` | `bool` | Whether return value is awaitable |
| `blocking` | `bool` | Whether blocks event loop |
| `cancellation` | `CancellationSpec` | Cancellation behavior (cooperative, immediate, none) |

#### Key Types

- **CancellationSpec**: `mode` (cooperative/immediate/none), `cleanup`, `propagates`
- **LifecycleSpec**: `states` (with terminal flags), `initial_state`, `transitions`
- **SyncSpec**: `primitive` (mailbox/channel/lock/semaphore), `semantics`, `capacity`, `backpressure`
- **SchedulingSpec**: `executor` (event_loop/thread_pool/process_pool), `priority`, `timeout`

#### Example

```json
{
  "extensions": ["async"],
  "library": {
    "types": [{
      "name": "Actor",
      "kind": "class",
      "module": "mylib.runtime",
      "lifecycle": {
        "states": [
          {"name": "INIT", "description": "Created but not started"},
          {"name": "RUNNING", "description": "Actively processing"},
          {"name": "COMPLETED", "terminal": true}
        ],
        "initial_state": "INIT",
        "transitions": [
          {"from": "INIT", "to": "RUNNING", "trigger": "start()"},
          {"from": "RUNNING", "to": "COMPLETED", "trigger": "normal completion"}
        ]
      },
      "methods": [{
        "name": "run",
        "signature": "(self) -> T",
        "async": true,
        "cancellation": {"mode": "cooperative", "cleanup": "Resources released"}
      }]
    }]
  }
}
```

---

### cli

**Purpose**: Define command-line interface specifications including commands, arguments, options, shell completion, and exit codes.

**Enable**: `"extensions": ["cli"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `cli_name` | `str` | CLI executable name |
| `commands` | `CommandSpec[]` | Top-level commands |
| `global_options` | `OptionSpec[]` | Options available to all commands |
| `shell_completion` | `ShellCompletionSpec` | Shell completion configuration |
| `help_formatting` | `HelpFormattingSpec` | Help text formatting |
| `exit_codes` | `ExitCodeSpec[]` | Exit code definitions |

#### Key Types

- **CommandSpec**: `name`, `handler`, `arguments`, `options`, `subcommands` (recursive), `examples`
- **ArgumentSpec**: `name`, `type`, `required`, `nargs`, `envvar`, `shell_complete`
- **OptionSpec**: `name`, `short`, `type`, `is_flag`, `count`, `multiple`, `choices`, `prompt`
- **ExitCodeSpec**: `code`, `name`, `description`

#### Example

```json
{
  "extensions": ["cli"],
  "library": {
    "cli_name": "myapp",
    "commands": [{
      "name": "run",
      "handler": "myapp.cli:run_command",
      "arguments": [
        {"name": "config", "type": "Path", "required": true}
      ],
      "options": [
        {"name": "verbose", "short": "v", "is_flag": true, "count": true},
        {"name": "output", "short": "o", "type": "Path", "default": "stdout"}
      ],
      "examples": [
        {"command": "myapp run config.yaml -vv", "description": "Run with verbose output"}
      ]
    }],
    "exit_codes": [
      {"code": 0, "name": "SUCCESS", "description": "Successful execution"},
      {"code": 1, "name": "ERROR", "description": "General error"}
    ]
  }
}
```

---

### config

**Purpose**: Define configuration management including settings, sources, profiles, and secrets handling.

**Enable**: `"extensions": ["config"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `settings` | `SettingSpec[]` | Configuration settings |
| `config_sources` | `ConfigSourcesSpec` | Source priority and loading |
| `profiles` | `ProfileSpec[]` | Configuration profiles (dev, prod) |
| `secrets` | `SecretsSpec` | Secrets handling configuration |

#### Key Types

- **SettingSpec**: `name`, `type`, `default`, `env_var`, `cli_flag`, `validation`, `secret`, `choices`
- **ConfigSourcesSpec**: `priority` (cli/env/file/defaults), `file_formats`, `paths`, `env_prefix`
- **ProfileSpec**: `name`, `inherits`, `overrides`, `env_var_trigger`
- **SecretsSpec**: `fields`, `storage` (env/keyring/vault/aws_secrets), `masking`

#### Example

```json
{
  "extensions": ["config"],
  "library": {
    "settings": [
      {"name": "host", "type": "str", "default": "localhost", "env_var": "MYAPP_HOST"},
      {"name": "port", "type": "int", "default": 8080, "validation": "gt(0)"},
      {"name": "api_key", "type": "str", "required": true, "secret": true}
    ],
    "config_sources": {
      "priority": ["cli", "env", "file", "defaults"],
      "file_formats": ["toml", "yaml"],
      "env_prefix": "MYAPP_"
    },
    "profiles": [
      {"name": "development", "overrides": {"host": "localhost"}},
      {"name": "production", "inherits": "development", "overrides": {"host": "0.0.0.0"}}
    ]
  }
}
```

---

### data

**Purpose**: Model data processing including dtypes, transforms, pipelines, evaluation strategies, and I/O formats.

**Enable**: `"extensions": ["data"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `dtypes` | `DTypeSpec[]` | Supported data types |
| `transforms` | `TransformSpec[]` | Transformation operations |
| `pipelines` | `PipelineSpec[]` | Pipeline definitions |
| `io_formats` | `IOFormatSpec[]` | I/O format support |
| `evaluation_strategy` | `EvaluationStrategySpec` | Lazy vs eager evaluation |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `dtype_behavior` | `DTypeBehaviorSpec` | Type coercion and inference |
| `method_chaining` | `MethodChainingSpec` | Fluent API support |
| `memory_layout` | `MemoryLayoutSpec` | Memory layout (row/column major) |
| `parallelism` | `ParallelismSpec` | Parallelism support |

#### Method Fields

| Field | Type | Description |
|-------|------|-------------|
| `lazy` | `bool` | Lazily evaluated |
| `in_place` | `bool` | Modifies data in place |
| `copy_semantics` | `enum` | copy, view, copy_on_write |
| `parallelizable` | `bool` | Can be parallelized |

#### Example

```json
{
  "extensions": ["data"],
  "library": {
    "dtypes": [
      {"name": "Int64", "category": "numeric", "nullable": true, "bit_width": 64},
      {"name": "Utf8", "category": "string", "nullable": true}
    ],
    "transforms": [
      {"name": "filter", "category": "filter", "preserves_order": true},
      {"name": "groupby", "category": "aggregate", "preserves_order": false}
    ],
    "evaluation_strategy": {
      "default": "lazy",
      "eager_triggers": ["collect", "to_pandas"],
      "query_optimization": true
    },
    "io_formats": [
      {"format": "parquet", "streaming": true, "compression": ["snappy", "zstd"]}
    ]
  }
}
```

---

### events

**Purpose**: Model event-driven architecture including events, handlers, topics, sagas, and event bus configuration.

**Enable**: `"extensions": ["events"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `events` | `EventSpec[]` | Event type definitions |
| `handlers` | `HandlerSpec[]` | Event handler definitions |
| `event_bus` | `EventBusSpec` | Event bus configuration |
| `topics` | `TopicSpec[]` | Topic/channel definitions |
| `sagas` | `SagaSpec[]` | Saga/process manager definitions |

#### Type/Method Fields

| Field | Type | Description |
|-------|------|-------------|
| `emits` | `str[]` | Events this type/method emits |
| `handles` | `str[]` | Events this type handles |
| `triggers_on` | `str[]` | Events that trigger this method |

#### Key Types

- **EventSpec**: `name`, `category` (domain/integration/notification), `payload`, `topic`, `idempotency_key`
- **HandlerSpec**: `name`, `handles`, `function`, `retry`, `timeout`, `idempotent`, `dead_letter`
- **EventBusSpec**: `type` (in_memory/redis/kafka), `guaranteed_delivery`, `ordering_guarantee`
- **SagaSpec**: `name`, `starts_with`, `steps`, `compensations`, `persistence`

#### Example

```json
{
  "extensions": ["events"],
  "library": {
    "events": [{
      "name": "OrderCreated",
      "category": "domain",
      "payload": [
        {"name": "order_id", "type": "str", "required": true},
        {"name": "total", "type": "Decimal"}
      ],
      "topic": "orders"
    }],
    "handlers": [{
      "name": "process_order",
      "handles": ["OrderCreated"],
      "function": "mylib.handlers:process_order",
      "retry": {"max_attempts": 3, "backoff": "exponential"},
      "idempotent": true
    }],
    "event_bus": {
      "type": "kafka",
      "guaranteed_delivery": true,
      "ordering_guarantee": "per_partition"
    }
  }
}
```

---

### orm

**Purpose**: Model object-relational mapping including database models, relationships, constraints, and migrations.

**Enable**: `"extensions": ["orm"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `models` | `ModelSpec[]` | ORM model definitions |
| `session_management` | `SessionManagementSpec` | Session configuration |
| `query_patterns` | `QueryPatternSpec[]` | Common query patterns |
| `migrations` | `MigrationSpec` | Migration configuration |
| `database_support` | `DatabaseSupportSpec[]` | Supported databases |

#### Key Types

- **ModelSpec**: `name`, `table`, `columns`, `relationships`, `indexes`, `constraints`, `polymorphic`
- **ColumnSpec**: `name`, `type`, `nullable`, `primary_key`, `foreign_key`, `on_delete`
- **RelationshipSpec**: `name`, `type` (one_to_one/one_to_many/many_to_many), `target`, `lazy`, `cascade`
- **MigrationSpec**: `tool` (alembic/flyway), `directory`, `auto_generate`

#### Example

```json
{
  "extensions": ["orm"],
  "library": {
    "models": [{
      "name": "User",
      "table": "users",
      "columns": [
        {"name": "id", "type": "Integer", "primary_key": true, "auto_increment": true},
        {"name": "email", "type": "String(255)", "unique": true, "nullable": false},
        {"name": "created_at", "type": "DateTime", "server_default": "now()"}
      ],
      "relationships": [
        {"name": "posts", "type": "one_to_many", "target": "Post", "back_populates": "author"}
      ],
      "indexes": [
        {"columns": ["email"], "unique": true}
      ]
    }],
    "migrations": {
      "tool": "alembic",
      "directory": "migrations/",
      "auto_generate": true
    }
  }
}
```

---

### plugins

**Purpose**: Model plugin systems including extension points, hooks, registries, and plugin discovery mechanisms.

**Enable**: `"extensions": ["plugins"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `extension_points` | `ExtensionPointSpec[]` | Extension point definitions |
| `hooks` | `HookSpec[]` | Hook definitions |
| `registries` | `RegistrySpec[]` | Plugin registries |
| `discovery` | `DiscoverySpec` | Plugin discovery configuration |
| `builtin_plugins` | `PluginSpec[]` | Built-in plugin definitions |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `extensible` | `bool` | Whether type is an extension point |
| `extension_of` | `str` | Extension point this type implements |
| `plugin_api` | `bool` | Whether part of plugin API |

#### Key Types

- **ExtensionPointSpec**: `name`, `interface`, `multiple`, `required`, `default`, `lifecycle`
- **HookSpec**: `name`, `type` (filter/action/event/wrapper), `signature`, `execution_order`
- **RegistrySpec**: `name`, `key_type`, `value_type`, `thread_safe`, `override_policy`
- **DiscoverySpec**: `mechanisms` (entry_points/namespace_packages/directory_scan), `auto_discover`

#### Example

```json
{
  "extensions": ["plugins"],
  "library": {
    "extension_points": [{
      "name": "formatters",
      "interface": "FormatterProtocol",
      "multiple": true,
      "priority_ordered": true
    }],
    "hooks": [{
      "name": "pre_format",
      "type": "filter",
      "signature": "(data: dict) -> dict",
      "execution_order": "pipeline"
    }],
    "discovery": {
      "mechanisms": [{"type": "entry_points", "entry_point_group": "mylib.plugins"}],
      "auto_discover": true
    }
  }
}
```

---

### serialization

**Purpose**: Model serialization patterns including formats, encoders/decoders, schemas, and type mappings.

**Enable**: `"extensions": ["serialization"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `serializers` | `SerializerSpec[]` | Serializer definitions |
| `schemas` | `SchemaSpec[]` | Schema definitions |
| `type_mappings` | `TypeMappingSpec[]` | Python to serialized type mappings |
| `encoder_registry` | `EncoderRegistrySpec` | Custom encoder registry |
| `settings` | `SerializationSettingsSpec` | Global serialization settings |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `serializable` | `bool` | Whether type is serializable |
| `serialize_as` | `str` | Type to serialize as |
| `exclude_fields` | `str[]` | Fields to exclude from serialization |
| `field_aliases` | `dict` | Field name mappings |

#### Key Types

- **SerializerSpec**: `name`, `format` (json/yaml/msgpack/protobuf), `options`, `type_handlers`
- **SchemaSpec**: `name`, `format` (json_schema/openapi/avro), `fields`, `strict`
- **SerializationSettingsSpec**: `default_format`, `naming_convention`, `datetime_format`

#### Example

```json
{
  "extensions": ["serialization"],
  "library": {
    "serializers": [{
      "name": "json",
      "format": "json",
      "naming_convention": "camel_case",
      "datetime_format": "iso8601",
      "null_handling": "exclude"
    }],
    "type_mappings": [
      {"python_type": "datetime", "serialized_type": "string", "bidirectional": true}
    ],
    "settings": {
      "default_format": "json",
      "validation_mode": "strict"
    }
  }
}
```

---

### state

**Purpose**: Model state management patterns including Redux/MobX stores, XState-style state machines, and middleware.

**Enable**: `"extensions": ["state"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `stores` | `StoreSpec[]` | State store definitions |
| `state_machines` | `StateMachineSpec[]` | State machine definitions |
| `actions` | `ActionSpec[]` | Action definitions |
| `selectors` | `SelectorSpec[]` | State selectors |
| `middleware` | `StateMiddlewareSpec[]` | Middleware definitions |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `state_shape` | `StateShapeSpec` | State structure (normalized, entities) |
| `immutable` | `bool` | Whether state is immutable |

#### Key Types

- **StoreSpec**: `name`, `type` (redux/mobx/zustand), `state_type`, `reducers`, `slices`, `persistence`
- **StateMachineSpec**: `name`, `states`, `initial`, `transitions`, `guards`, `actions`, `services`
- **MachineStateSpec**: `name`, `type` (atomic/compound/parallel/final), `on`, `entry`, `exit`
- **ActionSpec**: `name`, `type`, `payload_type`, `creator`, `async`

#### Example

```json
{
  "extensions": ["state"],
  "library": {
    "state_machines": [{
      "name": "checkout",
      "initial": "cart",
      "states": [
        {"name": "cart", "on": {"CHECKOUT": "shipping"}},
        {"name": "shipping", "on": {"CONFIRM": "payment"}},
        {"name": "payment", "on": {"PAY": "complete"}},
        {"name": "complete", "type": "final"}
      ],
      "guards": [{"name": "hasItems", "function": "mylib.guards:has_items"}]
    }],
    "actions": [
      {"name": "addItem", "type": "cart/addItem", "payload_type": "Product"}
    ]
  }
}
```

---

### testing

**Purpose**: Model testing infrastructure including pytest fixtures, mocks, factories, and coverage configuration.

**Enable**: `"extensions": ["testing"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `fixtures` | `FixtureSpec[]` | Pytest fixture definitions |
| `markers` | `MarkerSpec[]` | Custom pytest markers |
| `conftest_files` | `ConftestSpec[]` | Conftest.py documentation |
| `mocks` | `MockSpec[]` | Mock/stub utilities |
| `factories` | `FactorySpec[]` | Test data factories |
| `coverage` | `CoverageSpec` | Coverage configuration |
| `pytest_plugins` | `PytestPluginConfig` | Plugin configuration |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `testable` | `bool` | Whether type is testable |
| `test_double` | `TestDoubleSpec` | Test double configuration |
| `golden_tests` | `str[]` | Golden test file paths |

#### Key Types

- **FixtureSpec**: `name`, `scope` (function/class/module/session), `factory`, `autouse`, `async`
- **MockSpec**: `name`, `type` (mock/stub/spy/fake), `target`, `auto_spec`
- **FactorySpec**: `name`, `model`, `fields`, `traits`, `sequences`
- **MarkerSpec**: `name`, `args`, `skip_reason`, `xfail_reason`

#### Example

```json
{
  "extensions": ["testing"],
  "library": {
    "fixtures": [
      {"name": "db", "scope": "session", "factory": "tests.fixtures:create_db", "yields": true},
      {"name": "client", "scope": "function", "dependencies": ["db"], "async": true}
    ],
    "factories": [{
      "name": "UserFactory",
      "model": "User",
      "fields": [
        {"name": "email", "faker": "email"},
        {"name": "id", "sequence": "user_{n}"}
      ],
      "traits": [
        {"name": "admin", "overrides": {"role": "admin"}}
      ]
    }],
    "markers": [
      {"name": "slow", "description": "Marks tests as slow"},
      {"name": "integration", "description": "Integration tests"}
    ],
    "coverage": {
      "tool": "pytest-cov",
      "targets": [{"path": "src/", "minimum": 80}],
      "branch_coverage": true
    }
  }
}
```

---

### web

**Purpose**: Model web framework specifications including routes, middleware, dependencies, and WebSockets.

**Enable**: `"extensions": ["web"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `routes` | `RouteSpec[]` | HTTP route definitions |
| `middleware` | `MiddlewareSpec[]` | Middleware definitions |
| `dependencies` | `DependencySpec[]` | Dependency injection |
| `websockets` | `WebSocketSpec[]` | WebSocket endpoints |
| `error_handlers` | `ErrorHandlerSpec[]` | Exception to HTTP mappings |

#### Key Types

- **RouteSpec**: `path`, `method`, `handler`, `path_params`, `query_params`, `request_body`, `response`, `auth`, `rate_limit`
- **MiddlewareSpec**: `name`, `type`, `order`, `applies_to` (all/tagged/specific), `position`
- **DependencySpec**: `name`, `type`, `factory`, `scope` (request/session/app/singleton), `cacheable`
- **RateLimitSpec**: `requests`, `window`, `key`, `burst`

#### Example

```json
{
  "extensions": ["web"],
  "library": {
    "routes": [{
      "path": "/users/{user_id}",
      "method": "get",
      "handler": "mylib.api:get_user",
      "path_params": [{"name": "user_id", "type": "int"}],
      "response": {"type": "User", "status": 200},
      "errors": [{"status": 404, "exception": "NotFoundError"}],
      "auth": "required"
    }],
    "middleware": [
      {"name": "cors", "type": "mylib.middleware:CORSMiddleware", "order": 0},
      {"name": "auth", "type": "mylib.middleware:AuthMiddleware", "order": 10}
    ],
    "dependencies": [{
      "name": "db_session",
      "factory": "mylib.deps:get_db",
      "scope": "request",
      "async": true
    }]
  }
}
```

---

## Concern Extensions

### errors

**Purpose**: Document error handling including exception hierarchies, error codes, and recovery strategies.

**Enable**: `"extensions": ["errors"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `error_hierarchy` | `ErrorHierarchyNode[]` | Exception class hierarchy |
| `exceptions` | `ExceptionSpec[]` | Detailed exception specs |
| `error_codes` | `ErrorCode[]` | Enumerated error codes |

#### Key Types

- **ErrorHierarchyNode**: `type`, `base`, `description`, `children`
- **ExceptionSpec**: `type`, `module`, `base`, `fields`, `raised_by`, `recovery`, `retryable`
- **ErrorCode**: `code`, `type`, `category`, `description`, `docs_url`, `severity`

#### Example

```json
{
  "extensions": ["errors"],
  "library": {
    "error_hierarchy": [{
      "type": "MyLibError",
      "base": "Exception",
      "children": ["ConnectionError", "ValidationError"]
    }],
    "exceptions": [{
      "type": "ConnectionError",
      "module": "mylib.errors",
      "base": "MyLibError",
      "fields": [{"name": "host", "type": "str"}, {"name": "port", "type": "int"}],
      "recovery": "Check network and retry",
      "retryable": true
    }],
    "error_codes": [{
      "code": "E001",
      "type": "ConnectionError",
      "description": "Connection refused",
      "docs_url": "https://docs.mylib.dev/errors/E001"
    }]
  }
}
```

---

### workflow

**Purpose**: Add workflow orchestration on top of the core `maturity` field—defining gates, evidence requirements, and approval processes for maturity transitions.

**Enable**: `"extensions": ["workflow"]`

See [Workflow Extension](workflow.md) for comprehensive documentation including workflow definitions, evidence types, and lint rules.

#### Architecture: Layered Design

The workflow extension works on top of the core `maturity` field (see [Core Schema](core.md#entitymaturity)):

```
┌─────────────────────────────────────────────────────┐
│  Workflow Extension (Optional)                       │
│  • Workflows define HOW to progress through maturity │
│  • Gates: evidence/approval required per transition  │
│  • Evidence tracking for auditing/compliance         │
├─────────────────────────────────────────────────────┤
│  Core: maturity field (Always Available)             │
│  • WHERE is this in development                      │
│  • Fixed enum: idea → specified → ... → released     │
└─────────────────────────────────────────────────────┘
```

- **Without workflow**: Set `maturity` directly, no validation of transitions
- **With workflow**: Workflows define gates that must be satisfied to advance

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `workflows` | `WorkflowSpec[]` | Workflow definitions with maturity gates |
| `default_workflow` | `str` | Default workflow for entities |

#### Entity Fields (types, functions, features)

| Field | Type | Description |
|-------|------|-------------|
| `maturity` | `EntityMaturity` | Current maturity level (core field) |
| `workflow` | `str` | Workflow override for this entity |
| `maturity_evidence` | `EvidenceSpec[]` | Evidence supporting current maturity |

#### Workflow Structure

Workflows define gates for maturity transitions:

```json
{
  "name": "standard",
  "description": "Standard development workflow",
  "maturity_gates": [
    {
      "from_maturity": "designed",
      "to_maturity": "implemented",
      "gates": [{"type": "pr_merged", "required": true}]
    },
    {
      "from_maturity": "implemented",
      "to_maturity": "tested",
      "gates": [{"type": "tests_passing", "required": true}]
    }
  ]
}
```

#### Evidence Types

`pr`, `tests`, `design_doc`, `docs`, `approval`, `benchmark`, `migration_guide`, `deprecation_notice`, `custom`

#### Example

```json
{
  "extensions": ["workflow"],
  "library": {
    "default_workflow": "standard",
    "workflows": [{
      "name": "standard",
      "description": "Standard development workflow",
      "maturity_gates": [
        {
          "from_maturity": "designed",
          "to_maturity": "implemented",
          "gates": [{"type": "pr_merged", "required": true}]
        },
        {
          "from_maturity": "implemented",
          "to_maturity": "tested",
          "gates": [{"type": "tests_passing", "required": true}]
        }
      ]
    }],
    "types": [{
      "name": "DataProcessor",
      "kind": "class",
      "module": "mylib.processing",
      "maturity": "tested",
      "maturity_evidence": [
        {"type": "pr", "url": "https://github.com/org/repo/pull/42"},
        {"type": "tests", "path": "tests/test_processor.py"}
      ]
    }]
  }
}
```

---

### observability

**Purpose**: Document logging, metrics, distributed tracing, and health checks.

**Enable**: `"extensions": ["observability"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `logging` | `LoggingSpec` | Logging configuration |
| `metrics` | `MetricSpec[]` | Metrics exposed by library |
| `tracing` | `TracingSpec` | Distributed tracing configuration |
| `health_checks` | `HealthCheckSpec[]` | Health check endpoints |
| `debug_tools` | `DebugToolsSpec` | Debug tools configuration |

#### Key Types

- **LoggingSpec**: `logger_name`, `levels_used`, `structured`, `context_fields`, `sensitive_fields`
- **MetricSpec**: `name`, `type` (counter/gauge/histogram/summary), `labels`, `buckets`
- **TracingSpec**: `span_names`, `propagation` (w3c/b3/jaeger), `sampling`, `sampling_rate`
- **HealthCheckSpec**: `name`, `type` (liveness/readiness/startup), `endpoint`, `timeout`

#### Example

```json
{
  "extensions": ["observability"],
  "library": {
    "logging": {
      "logger_name": "mylib",
      "levels_used": ["DEBUG", "INFO", "WARNING", "ERROR"],
      "structured": true,
      "context_fields": ["request_id", "user_id"]
    },
    "metrics": [
      {"name": "mylib_requests_total", "type": "counter", "labels": ["method", "status"]},
      {"name": "mylib_request_duration_seconds", "type": "histogram", "buckets": [0.01, 0.1, 1.0]}
    ],
    "tracing": {
      "span_names": ["mylib.connect", "mylib.send"],
      "propagation": "w3c",
      "sampling": "probabilistic",
      "sampling_rate": 0.1
    },
    "health_checks": [
      {"name": "liveness", "type": "liveness", "endpoint": "/health/live"},
      {"name": "readiness", "type": "readiness", "endpoint": "/health/ready", "dependencies": ["db"]}
    ]
  }
}
```

---

### perf

**Purpose**: Document performance characteristics including complexity, benchmarks, and scaling properties.

**Enable**: `"extensions": ["perf"]`

#### Method/Function Fields

| Field | Type | Description |
|-------|------|-------------|
| `complexity` | `ComplexitySpec` | Algorithm complexity |
| `benchmarks` | `BenchmarkSpec[]` | Benchmark results |
| `optimization_hints` | `str[]` | Usage optimization tips |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `memory_layout` | `MemoryLayoutSpec` | Memory layout characteristics |
| `scaling` | `ScalingSpec` | Scaling properties |

#### Key Types

- **ComplexitySpec**: `time`, `space`, `best_case`, `worst_case`, `amortized`
- **BenchmarkSpec**: `operation`, `input_size`, `mean`, `p95`, `p99`, `throughput`, `environment`
- **MemoryLayoutSpec**: `size_bytes`, `alignment`, `cache_friendly`, `slots`
- **ScalingSpec**: `horizontal`, `vertical`, `bottleneck`, `max_concurrent`

#### Example

```json
{
  "extensions": ["perf"],
  "library": {
    "functions": [{
      "name": "sort_items",
      "complexity": {
        "time": "O(n log n)",
        "space": "O(n)",
        "best_case": "O(n)",
        "worst_case": "O(n log n)"
      },
      "benchmarks": [{
        "operation": "sort 10k items",
        "input_size": "10000",
        "mean": 0.015,
        "p99": 0.025,
        "environment": "Python 3.11, M1 Mac"
      }],
      "optimization_hints": ["Pre-sort partially ordered data"]
    }],
    "types": [{
      "name": "DataBuffer",
      "memory_layout": {"size_bytes": 128, "cache_friendly": true, "slots": true},
      "scaling": {"horizontal": true, "max_concurrent": 1000}
    }]
  }
}
```

---

### safety

**Purpose**: Document thread safety, reentrancy, memory safety, and concurrency models.

**Enable**: `"extensions": ["safety"]`

#### Method/Function Fields

| Field | Type | Description |
|-------|------|-------------|
| `thread_safe` | `bool` | Whether thread-safe |
| `reentrant` | `bool` | Whether reentrant |
| `signal_safe` | `bool` | Safe in signal handlers |
| `atomic` | `bool` | Atomic operation |

#### Type Fields

| Field | Type | Description |
|-------|------|-------------|
| `thread_safety` | `ThreadSafetySpec` | Thread safety specification |
| `reentrancy` | `ReentrancySpec` | Reentrancy specification |
| `memory_safety` | `MemorySafetySpec` | Memory safety specification |
| `concurrency_model` | `ConcurrencyModelSpec` | Concurrency model |

#### Key Types

- **ThreadSafetySpec**: `safe`, `mode` (immutable/synchronized/lock_free), `lock_type`, `lock_granularity`
- **ReentrancySpec**: `reentrant`, `reason`, `safe_methods`, `unsafe_methods`
- **MemorySafetySpec**: `leaks`, `cleanup` (automatic/manual/context_manager), `cyclic_refs_safe`
- **ConcurrencyModelSpec**: `model` (shared_nothing/actor/csp), `deadlock_free`, `starvation_free`

#### Example

```json
{
  "extensions": ["safety"],
  "library": {
    "types": [{
      "name": "ConnectionPool",
      "thread_safety": {
        "safe": true,
        "mode": "synchronized",
        "lock_type": "rlock",
        "lock_granularity": "per_instance"
      },
      "memory_safety": {
        "leaks": "none",
        "cleanup": "context_manager",
        "cyclic_refs_safe": true
      },
      "concurrency_model": {
        "model": "shared_memory",
        "deadlock_free": true
      }
    }],
    "functions": [{
      "name": "atomic_increment",
      "thread_safe": true,
      "atomic": true
    }]
  }
}
```

---

### versioning

**Purpose**: Document API versioning, deprecation, and compatibility policies.

**Enable**: `"extensions": ["versioning"]`

#### Library Fields

| Field | Type | Description |
|-------|------|-------------|
| `api_version` | `str` | Current API version |
| `stability` | `enum` | stable, beta, alpha, experimental, deprecated |
| `deprecations` | `DeprecationSpec[]` | Deprecation notices |
| `breaking_changes` | `BreakingChangeSpec[]` | Breaking change history |
| `compatibility` | `CompatibilitySpec` | Compatibility policy |
| `changelog_url` | `str` | URL to changelog |

#### Type/Method Fields

| Field | Type | Description |
|-------|------|-------------|
| `since` | `str` | Version introduced |
| `deprecated_since` | `str` | Version deprecated |
| `removed_in` | `str` | Version removed |
| `stability` | `enum` | Stability level |

#### Key Types

- **DeprecationSpec**: `target`, `since`, `removed_in`, `replacement`, `migration`, `reason`
- **BreakingChangeSpec**: `version`, `change`, `affected`, `migration`, `codemod`
- **CompatibilitySpec**: `backward`, `forward`, `policy`, `semantic_versioning`

#### Example

```json
{
  "extensions": ["versioning"],
  "library": {
    "api_version": "2.0.0",
    "stability": "stable",
    "deprecations": [{
      "target": "#/types/OldClient",
      "since": "2.0.0",
      "removed_in": "3.0.0",
      "replacement": "#/types/NewClient",
      "migration": "Replace OldClient with NewClient, update constructor args"
    }],
    "breaking_changes": [{
      "version": "2.0.0",
      "change": "Removed legacy API",
      "affected": ["#/functions/legacy_connect"],
      "migration": "Use connect() instead"
    }],
    "compatibility": {
      "backward": "Minor versions are backward compatible",
      "semantic_versioning": {"major": "Breaking changes", "minor": "New features", "patch": "Bug fixes"}
    },
    "types": [{
      "name": "NewClient",
      "since": "2.0.0",
      "stability": "stable"
    }]
  }
}
```

---

## Extension Compatibility

All extensions are designed to be composable. This section highlights synergistic combinations.

### Semantic Relationships

| Extension A | Extension B | Interaction |
|-------------|-------------|-------------|
| `workflow` | `testing` | `workflow_state: tested` should align with test coverage |
| `workflow` | `versioning` | Deprecation evidence pairs with `deprecated_since` |
| `async` | `state` | Orthogonal: async describes runtime, state describes FSM APIs |
| `events` | `observability` | Event-emitting types benefit from metrics/tracing |
| `data` | `serialization` | Complementary: data validation + serialization formats |
| `errors` | `observability` | Error tracking integrates with observability metrics |

### async + state

These extensions describe different aspects and do not overlap:

- **async extension**: Models runtime object lifecycle (connection states, task states)
- **state extension**: Models state machine APIs the library exposes to users

A type can use both:

```json
{
  "extensions": ["async", "state"],
  "library": {
    "types": [{
      "name": "WorkflowEngine",
      "lifecycle": {
        "states": [{"name": "running"}, {"name": "stopped", "terminal": true}],
        "initial_state": "running"
      },
      "state_machines": [{
        "name": "document-workflow",
        "initial": "draft",
        "states": [{"name": "draft"}, {"name": "published", "type": "final"}]
      }]
    }]
  }
}
```

### workflow + versioning

Deprecation workflows benefit from combining workflow evidence with versioning metadata:

```json
{
  "extensions": ["workflow", "versioning"],
  "library": {
    "types": [{
      "name": "OldClient",
      "kind": "class",
      "module": "mylib.client",
      "maturity": "deprecated",
      "maturity_evidence": [{"type": "deprecation_notice", "reference": "CHANGELOG.md", "date": "2024-06-01"}],
      "deprecated_since": "2.0.0",
      "removed_in": "3.0.0",
      "replacement": "#/types/NewClient"
    }]
  }
}
```

---

## Common Extension Combinations

### Web API Library

```json
{"extensions": ["async", "errors", "web", "observability"]}
```

- `async`: Document async request handling
- `errors`: Define error responses and codes
- `web`: Specify endpoints, auth, CORS
- `observability`: Request tracing and metrics

### Data Processing Library

```json
{"extensions": ["data", "serialization", "errors", "perf"]}
```

- `data`: Validation rules and transformations
- `serialization`: JSON/protobuf/msgpack support
- `errors`: Validation and parsing errors
- `perf`: Complexity and throughput specs

### CLI Application

```json
{"extensions": ["cli", "config", "errors"]}
```

- `cli`: Commands, arguments, flags
- `config`: Configuration file formats
- `errors`: Exit codes and error messages

### State Management Library

```json
{"extensions": ["state", "events", "testing"]}
```

- `state`: Store and state machine definitions
- `events`: Action dispatching patterns
- `testing`: Store testing utilities

### Plugin-Based Library

```json
{"extensions": ["plugins", "workflow", "versioning"]}
```

- `plugins`: Extension points and hooks
- `workflow`: Track plugin API maturity
- `versioning`: Plugin API versioning

---

## Extension Precedence

When extensions define similar concepts, the more specific extension takes precedence for its domain:

1. **State models**: `state.py` defines `MachineStateSpec` for XState/FSM patterns; `async_.py` defines `AsyncStateSpec` for runtime object lifecycles; the core `maturity` field tracks development progress. These are distinct concepts—runtime state vs. user-facing FSM APIs vs. development stage.

2. **Schema merging**: When `validate_spec()` merges extension schemas, core schema definitions take precedence over extension definitions with the same name.

---

## Adding New Extensions

When creating a new extension, consider:

1. **Field naming**: Prefix extension-specific fields to avoid collisions
2. **Semantic scope**: Document whether the extension describes runtime behavior, development process, or API contracts
3. **Complementary extensions**: Identify which existing extensions pair well with yours
4. **Lint rules**: Consider adding cross-extension rules if semantic relationships exist
