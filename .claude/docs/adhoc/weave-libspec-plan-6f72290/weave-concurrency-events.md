# Weave Concurrency Primitives and Event System

## Scope
Documents Weave's structured concurrency runtime (Nursery, Channel, race primitives) and its event system, including event types, discriminated union structure, middleware protocols, and state change kinds.

## Overview
Weave provides typed, structured concurrency primitives for multi-agent orchestration alongside a comprehensive event system for observability. Concurrency is modeled on nurseries (structured via async context managers) and typed channels for inter-actor communication. Events are Pydantic discriminated unions emitted as state changes, tokens, tool calls, and lifecycle transitions. Middleware protocols (EventMiddleware, LLMMiddleware) enable cross-cutting concerns like redaction, approval flows, and observability.

## Key Locations

### Concurrency Primitives

#### Nursery — Structured Concurrency
- **File:** `/Users/case/projects/threads/weave_design.md:1963-2057`
- **Relevance:** Core structured concurrency abstraction; manages child actor lifecycle, enforces guarantees (FAIL_FAST/COLLECT_ERRORS error policies), handles cancellation, routes requests through handlers, manages nursery-scoped channels.

**Context hooks:**
- `weave_design.md:1966-1969` - NurseryErrorPolicy enum (FAIL_FAST, COLLECT_ERRORS)
- `weave_design.md:1970-2013` - Nursery class definition with `__aenter__`, `__aexit__`, `spawn()`, `gather()` methods
- `weave_design.md:1980-1994` - __aexit__ behavior: First failure cancels siblings (FAIL_FAST), or waits for all and collects Exception objects (COLLECT_ERRORS)
- `weave_design.md:1996-2013` - spawn() method signature and semantics
- `weave_design.md:2015-2025` - gather() method with FAIL_FAST/COLLECT_ERRORS behavior
- `weave_design.md:2027-2047` - channel() method for creating nursery-scoped typed channels with automatic lifecycle management
- `weave_design.md:2050-2056` - Responsibilities: child actor lifecycle, structured concurrency guarantees, child cancellation, request routing, channel management
- `weave_design.md:2059-2062` - Boundaries: only manages Weave actors (not PydanticAI graphs), does not influence LLM call frequency

#### Channel[T] — Typed Async Message Queue
- **File:** `/Users/case/projects/threads/weave_design.md:2064-2155`
- **Relevance:** In-session typed async channel for inter-actor communication with backpressure semantics; automatically closed when nursery exits.

**Context hooks:**
- `weave_design.md:2069-2100` - Channel[T] class with send(), recv(), close(), closed property, __aiter__() for async iteration
- `weave_design.md:2072-2077` - send(item: T) - enqueues item; v0 queues are unbounded (maxsize/backpressure planned for v1)
- `weave_design.md:2079-2084` - recv() - dequeues next item; raises ChannelClosedError if closed and empty
- `weave_design.md:2086-2091` - close() marks channel closed, prevents further sends
- `weave_design.md:2093-2095` - closed property as bool
- `weave_design.md:2097-2099` - __aiter__() yields items until closed and drained
- `weave_design.md:2102` - Timeout note: recv() does not accept timeout; use asyncio.wait_for() for timeout behavior
- `weave_design.md:2104-2106` - Events: channel_send, channel_recv, channel_closed, channel_recv_error, channel_wait_state emitted as STATE_CHANGE with channel_id, message_id, depth/latency metrics, correlation_id
- `weave_design.md:2151-2154` - Boundaries: no LLM calls, no history, pure concurrency, in-session only

#### race() and race_tagged() — Awaitable Racing
- **File:** `/Users/case/projects/threads/weave_design.md:2108-2143`
- **Relevance:** Race multiple awaitables; returns winner value and list of pending awaitables. Optional cancellation of losers.

**Context hooks:**
- `weave_design.md:2108-2123` - race(*aws: Awaitable[Any], cancel_others: bool = True) → tuple[Any, list[Awaitable[Any]]]
- `weave_design.md:2119-2122` - Semantics: If cancel_others=True (default), cancels remaining awaitables; they must tolerate CancelledError
- `weave_design.md:2126-2127` - race_tagged(cases: Mapping[Hashable, Awaitable[Any]], cancel_others: bool = True) → tuple[Hashable, Any, list[Awaitable[Any]]]
- `weave_design.md:2130` - Optional observability: emit STATE_CHANGE(kind="race_result") with winner_index/winner_tag, cancelled_count, pending_count
- `weave_design.md:2134-2143` - Example usage: winner, pending = await weave.race(...), then manually cancel pending awaitables
- `weave_design.md:2146-2150` - Responsibilities: typed message queues, race resolution for multiple awaitables, backpressure semantics

### Event System

#### Event Model — Discriminated Union
- **File:** `/Users/case/projects/threads/weave_design.md:2311-2456`
- **Relevance:** Uniform event shape using Pydantic discriminated union (discriminator field: 'type'); supports tokens, tool calls, state changes, errors, lifecycle transitions.

**Context hooks:**
- `weave_design.md:2320-2338` - EventBase class: id (globally unique), seq (per-actor monotonic), actor_id, root_actor_id, parent_actor_id, timestamp, correlation_id
- `weave_design.md:2340-2342` - TokenEvent: type='TOKEN' (literal), payload: TokenPayload
- `weave_design.md:2345-2347` - ToolCallEvent: type='TOOL_CALL' (literal), payload: ToolCallPayload
- `weave_design.md:2351-2354` - Event union: Annotated[Union[TokenEvent, ToolCallEvent, ToolResultEvent, BroadcastEvent, ThoughtEvent, StateChangeEvent, ErrorEvent, LifecycleEvent], Field(discriminator='type')]
- `weave_design.md:2409-2418` - Responsibilities: uniform event shape, power Handle.stream() and trace/replay, EventBus broadcast fan-out (multiple subscribers observe without consuming), core bus receives every event before middleware
- `weave_design.md:2420-2426` - Boundaries: event payloads are free-form but documented per type, structure is internal ABI, external UI protocols are adapters, correlation_id tracks single thread of work, each payload carries typed ID (llm_call_id, message_id, channel_id, request_key, section_id)

#### Event Types — Literals and Discriminators
- **File:** `/Users/case/projects/threads/weave_design.md:2340-2354`
- **Relevance:** Eight event types with type discriminator field; each has specific payload structure.

**Event type definitions:**
- TokenEvent: type='TOKEN', payload: TokenPayload
- ToolCallEvent: type='TOOL_CALL', payload: ToolCallPayload
- ToolResultEvent: (implied) type='TOOL_RESULT', payload: ToolResultPayload
- BroadcastEvent: (implied) type='BROADCAST', payload: BroadcastPayload
- ThoughtEvent: (implied) type='THOUGHT', payload: ThoughtPayload
- StateChangeEvent: (implied) type='STATE_CHANGE', payload: StateChangePayload (with kind discriminator)
- ErrorEvent: (implied) type='ERROR', payload: ErrorPayload
- LifecycleEvent: (implied) type='LIFECYCLE', payload: LifecyclePayload

#### StateChangeKind Enum — 30+ Discriminator Values
- **File:** `/Users/case/projects/threads/weave_design.md:2356-2405`
- **Relevance:** Discriminator enum for StateChangeEvent; explicit values for all concurrency, channel, request, lifecycle, code execution, and routing operations.

**Complete StateChangeKind values:**

Mailbox operations:
- `MAILBOX_SEND = "mailbox_send"`
- `MAILBOX_RECEIVE = "mailbox_receive"`
- `MAILBOX_TIMEOUT = "mailbox_timeout"`
- `MAILBOX_WAIT_STATE = "mailbox_wait_state"`

Channel operations:
- `CHANNEL_SEND = "channel_send"`
- `CHANNEL_RECV = "channel_recv"`
- `CHANNEL_CLOSED = "channel_closed"`
- `CHANNEL_RECV_ERROR = "channel_recv_error"`
- `CHANNEL_WAIT_STATE = "channel_wait_state"`

Request slot operations:
- `REQUEST_REGISTERED = "request_registered"`
- `REQUEST_FULFILLED = "request_fulfilled"`
- `REQUEST_TIMED_OUT = "request_timed_out"`
- `REQUEST_CANCELLED = "request_cancelled"`
- `REQUEST_ABORTED_ON_RESTART = "request_aborted_on_restart"`
- `REQUEST_LATE_RESPONSE = "request_late_response"`
- `REQUEST_WAIT_STATE = "request_wait_state"`

Human-in-the-loop:
- `ASK_USER = "ask_user"`

Nursery lifecycle:
- `NURSERY_CREATED = "nursery_created"`
- `NURSERY_CHILD_SPAWNED = "nursery_child_spawned"`
- `NURSERY_EXIT = "nursery_exit"`

Code execution lifecycle:
- `CODE_EXECUTION_START = "code_execution_start"`
- `CODE_EXECUTION_END = "code_execution_end"`
- `CODE_EXECUTION_ERROR = "code_execution_error"`
- `CODE_EXECUTION_TIMEOUT = "code_execution_timeout"`

Child request routing:
- `CHILD_REQUEST_RECEIVED = "child_request_received"`
- `CHILD_REQUEST_HANDLED = "child_request_handled"`
- `CHILD_REQUEST_ESCALATED = "child_request_escalated"`

Race operations (optional):
- `RACE_RESULT = "race_result"`

Layout updates:
- `SECTION_UPDATE = "section_update"`

LLM integration:
- `LLM_CALL_STARTED = "llm_call_started"`
- `LLM_TRANSCRIPT = "llm_transcript"`

Restart/supervision:
- `RESTART_INITIATED = "restart_initiated"`
- `RESTART_COMPLETED = "restart_completed"`
- `RESTART_EXHAUSTED = "restart_exhausted"`

Trace operations:
- `TRACE_TRUNCATION = "trace_truncation"`

#### StateChangeEvent Payload Schemas — Minimum Contract
- **File:** `/Users/case/projects/threads/weave_design.md:2428-2453`
- **Relevance:** Each kind value has required and optional fields for state change payloads.

**Context hooks:**
- `weave_design.md:2430-2453` - Table of kind values with required/optional fields and notes:
  - mailbox_send: message_id, from_actor_id, to_actor_id, depth_after:int | Optional: size_bytes, redacted:bool
  - mailbox_receive: message_id, actor_id, from_actor_id?, depth_after:int | Optional: latency_ms
  - mailbox_timeout: actor_id, depth:int, wait_ms
  - mailbox_wait_state: actor_id, state:"waiting"|"completed"|"timeout", started_at, duration_ms?
  - channel_send: channel_id, message_id, actor_id, depth_after:int
  - channel_recv: channel_id, message_id, actor_id, depth_after:int | Optional: latency_ms
  - channel_closed: channel_id, actor_id
  - channel_recv_error: channel_id, actor_id, error_type="ChannelClosedError"
  - channel_wait_state: channel_id, actor_id, state:"waiting"|"completed"|"timeout", started_at, duration_ms?
  - request_registered: request_key, actor_id, expires_at?
  - request_fulfilled: request_key, actor_id, duration_ms?, payload_redacted:bool?
  - request_timed_out: request_key, actor_id, duration_ms?
  - request_cancelled: request_key, actor_id
  - request_aborted_on_restart: request_key, actor_id
  - request_late_response: request_key, actor_id, latency_ms?
  - request_wait_state: request_key, actor_id, state:"waiting"|"completed"|"timeout", started_at, duration_ms?
  - ask_user: request_key, actor_id, prompt, parse_as?
  - nursery_created: nursery_id, actor_id, error_policy
  - nursery_child_spawned: nursery_id, actor_id, child_actor_id
  - nursery_exit: nursery_id, actor_id, child_count, ok_count, failed_count, cancelled_count, error_policy
  - race_result (optional): winner_index, winner_tag?, cancelled_count, pending_count
  - section_update: section_id, action, version?, label?, tool_call_id?, plus action-specific fields (ranges, patch, content, path)

### Middleware Protocols

#### EventMiddleware Protocol
- **File:** `/Users/case/projects/threads/weave_design.md:2461-2477`
- **Relevance:** Protocol for observing immutable events; does not block core event delivery; exceptions are caught and surfaced as ErrorEvents but do not prevent original event propagation.

**Context hooks:**
- `weave_design.md:2461-2477` - EventMiddleware.__call__(event: Event, ctx: Context, next: Callable[[Event], Awaitable[None]]) → None
- `weave_design.md:2468-2476` - Semantics: observe immutable events, call await next(event) to continue, exceptions caught and surfaced as ErrorEvents but do NOT prevent original event from reaching core bus/trace/UI, pass modified copy to next() for downstream subscribers to see altered event

#### LLMMiddleware Protocol
- **File:** `/Users/case/projects/threads/weave_design.md:2480-2512`
- **Relevance:** Protocol for intercepting LLM and tool calls; before_llm receives LLMCallParams by default or full LLMRequest if llm_middleware_agent_scope=True in ActorOptions.

**Context hooks:**
- `weave_design.md:2480-2512` - LLMMiddleware protocol with before_llm(), after_llm(), before_tool(), after_tool()
- `weave_design.md:2489-2502` - before_llm(ctx: Context, call: LLMCallParams | LLMRequest) → LLMCallParams | LLMRequest | None
  - Returns: call object (modified or unmodified), None (proceed with unmodified), or raise exception to deny
  - Default scoping: LLMCallParams (call-level fields only)
  - Agent-scope option: full LLMRequest (model, instructions, deps, toolsets, builtin_tools)
- `weave_design.md:2504-2505` - after_llm(ctx: Context, result: LLMResult[Any]) → None
- `weave_design.md:2507-2508` - before_tool(ctx: Context, call: ToolCall) → ToolCall | None
- `weave_design.md:2510-2511` - after_tool(ctx: Context, result: ToolResult) → None
- `weave_design.md:2514-2523` - Example: RequireTicket middleware checking ctx.metadata.extra.get("ticket") for delete_user tool calls
- `weave_design.md:2533-2547` - Scoping: LLMCallParams default contains input, history, layout, response_type, model_settings, usage_limits, usage, deferred_tool_results, engine_overrides (NOT agent identity); opt-in with llm_middleware_agent_scope=True to receive full LLMRequest
- `weave_design.md:2549-2553` - Use cases for agent_scope=True: dynamic model routing, A/B testing system prompts, runtime tool injection
- `weave_design.md:2554` - Security note: agent-scope middleware can fundamentally alter agent behavior; use with caution and audit logging

#### Middleware Ordering and Routing
- **File:** `/Users/case/projects/threads/weave_design.md:2525-2529`
- **Relevance:** LLMMiddleware runs before execution; EventMiddleware runs after core bus publication. Both can be configured globally via set_default_middleware() or per-actor in ActorOptions.

**Context hooks:**
- `weave_design.md:2525-2529` - Ordering: LLMMiddleware.before_llm() MUST return call object (modified or unmodified) or raise; EventMiddleware runs after core bus and cannot block core delivery
- `weave_design.md:2529` - Configuration: ActorOptions accept both middleware lists; global defaults via set_default_middleware(event=..., llm=...)

#### LLMCallParams vs LLMRequest
- **File:** `/Users/case/projects/threads/weave_design.md:2531-2554`
- **Relevance:** LLMCallParams is call-level Weave-owned data; LLMRequest includes agent-level PydanticAI identity. Middleware scoping enforces ownership boundary.

**Context hooks:**
- `weave_design.md:2533-2537` - LLMCallParams default fields: input, history, layout, response_type, model_settings, usage_limits, usage, deferred_tool_results, engine_overrides
- `weave_design.md:2538` - Ownership boundary: Weave controls per-call context, PydanticAI controls Agent identity
- `weave_design.md:2540-2547` - Opt-in for agent-level access: @actor(llm_middleware_agent_scope=True, llm_middleware=(...)) to receive model, instructions, deps, toolsets, builtin_tools in before_llm()

## Relationships

- **PydanticAI Integration**: Nurseries and Channels are complementary to PydanticAI graphs; nurseries handle runtime-determined concurrency and fan-out/fan-in, graphs handle declarative state machines within agents. Events from ctx.act() trigger LLM middleware and flow through event middleware.
- **Request Routing**: Child requests from executed code can override handlers per-actor or use nursery-level handler; routes through handler chain before escalating to terminal→ask_user.
- **Trace/Replay**: EventBase.seq is monotonic per actor and preserved in Handle.stream() ordering; events power trace reconstruction and replay.
- **Code Execution**: Generated code can spawn actors in nurseries, create channels, make requests; emit LIFECYCLE, TOKEN, TOOL_CALL, TOOL_RESULT, BROADCAST events; bracketed by CODE_EXECUTION_START/END lifecycle events.
- **Observability**: Channel operations (send/recv/closed), mailbox operations (send/receive/timeout), request lifecycle (registered/fulfilled/timed_out/cancelled), and race results emit STATE_CHANGE events with metrics (latency_ms, depth_after, duration_ms).

## Open Questions

- How are ToolResultEvent, BroadcastEvent, ThoughtEvent, ErrorEvent, and LifecycleEvent payloads structured? (Document only specifies TokenEvent and ToolCallEvent; others implied in union)
- What fields comprise TokenPayload and ToolCallPayload? (Referenced but not defined in provided section)
- What is the full type definition of LLMRequest (lines 2567-2597 shown but question about how engine_overrides dict is validated/used)
- How does WeaveEventStream adapter translate AgentStreamEvent → Event in practice? (Mentioned but not shown in provided section)
- What are the semantics of correlation_id when not explicitly set during channel/request operations?
- Does StateChangeEvent have additional fields beyond the kind discriminator and payload, or is it strictly kind + payload?
- How are concurrent StateChangeEvents from different actors ordered in the core bus if timestamps are system-local?

