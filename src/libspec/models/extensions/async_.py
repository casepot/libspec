"""Async extension models for libspec specifications.

This module defines models for async/concurrent system semantics:
- Lifecycle states and transitions
- Cancellation handling
- Synchronization primitives
- Observable/stream semantics
- Execution scheduling
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import Field

from libspec.models.base import ExtensionModel
from libspec.models.types import NonEmptyStr


class CancellationMode(Enum):
    """How async operations handle cancellation requests.

    - cooperative: Operation checks for cancellation explicitly
    - immediate: Cancellation interrupts operation immediately
    - none: No cancellation support
    """

    cooperative = 'cooperative'
    immediate = 'immediate'
    none = 'none'


class CancellationSpec(ExtensionModel):
    mode: CancellationMode | None = Field(None, description='Cancellation mode')
    cleanup: str | None = Field(
        None, description='What cleanup happens on cancellation'
    )
    propagates: bool | None = Field(
        True, description='Whether cancellation propagates to children'
    )


class AsyncStateSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='State name')
    description: str | None = Field(None, description='What this state represents')
    terminal: bool | None = Field(False, description='Whether this is a terminal state')
    on_enter: str | None = Field(
        None, description='Action to run on entering this state'
    )
    on_exit: str | None = Field(None, description='Action to run on exiting this state')


class AsyncTransitionSpec(ExtensionModel):
    from_: NonEmptyStr = Field(default=..., alias='from', description='Source state name')
    to: NonEmptyStr = Field(default=..., description='Target state name')
    trigger: str = Field(
        default=..., description='What causes this transition (method call, event, etc.)'
    )
    guard: str | None = Field(
        None, description='Condition that must be true for transition'
    )
    side_effects: list[str] | None = Field(
        None, description='Side effects of this transition'
    )


class Primitive(Enum):
    """Type of synchronization primitive for concurrent access.

    - mailbox: Actor-style message passing
    - channel: Go-style typed communication channel
    - lock: Mutual exclusion lock
    - semaphore: Counting semaphore for resource limits
    - event: One-shot or multi-shot signaling
    - barrier: Synchronization point for multiple tasks
    - condition: Wait/notify coordination
    """

    mailbox = 'mailbox'
    channel = 'channel'
    lock = 'lock'
    semaphore = 'semaphore'
    event = 'event'
    barrier = 'barrier'
    condition = 'condition'


class Semantics(Enum):
    """Ordering and delivery semantics for message passing.

    - fifo: First-in, first-out ordering
    - priority: Priority-based ordering
    - broadcast: Message delivered to all subscribers
    - lifo: Last-in, first-out (stack) ordering
    """

    fifo = 'fifo'
    priority = 'priority'
    broadcast = 'broadcast'
    lifo = 'lifo'


class SyncBackpressure(Enum):
    """How synchronization primitives handle capacity limits.

    - block: Block sender until space available
    - drop: Silently discard new items
    - error: Raise an error when full
    """

    block = 'block'
    drop = 'drop'
    error = 'error'


class SyncSpec(ExtensionModel):
    primitive: Primitive | None = Field(
        None, description='Type of synchronization primitive'
    )
    semantics: Semantics | None = Field(None, description='Ordering/delivery semantics')
    bounded: bool | None = Field(
        None, description='Whether the primitive has a capacity limit'
    )
    capacity: Annotated[int, Field(ge=0)] | None = Field(
        default=None, description='Maximum capacity (if bounded)'
    )
    backpressure: SyncBackpressure | None = Field(
        None, description='What happens when capacity is reached'
    )


class Kind(Enum):
    """Observable stream temperature (hot vs cold).

    - hot: Emits regardless of subscribers; late subscribers miss events
    - cold: Waits for subscription; each subscriber gets all events
    """

    hot = 'hot'
    cold = 'cold'


class ObservableBackpressure(Enum):
    """How observables handle slow consumers.

    - buffer: Buffer items until consumer catches up
    - drop: Drop new items when buffer is full
    - block: Block producer until consumer catches up
    - error: Signal error when buffer overflows
    - latest: Keep only the latest item, dropping older ones
    """

    buffer = 'buffer'
    drop = 'drop'
    block = 'block'
    error = 'error'
    latest = 'latest'


class ObservableSpec(ExtensionModel):
    kind: Kind | None = Field(
        None, description='Hot (live) or cold (replay) observable'
    )
    backpressure: ObservableBackpressure | None = Field(
        None, description='Backpressure strategy'
    )
    replay: bool | None = Field(
        None, description='Whether late subscribers receive past events'
    )
    replay_buffer: Annotated[int, Field(ge=0)] | None = Field(
        default=None, description='Number of past events to replay'
    )
    multicasting: bool | None = Field(
        None, description='Whether multiple subscribers share the same stream'
    )


class Executor(Enum):
    """Where async operations are executed.

    - event_loop: Single-threaded asyncio event loop
    - thread_pool: ThreadPoolExecutor for I/O-bound work
    - process_pool: ProcessPoolExecutor for CPU-bound work
    - custom: Custom executor implementation
    """

    event_loop = 'event_loop'
    thread_pool = 'thread_pool'
    process_pool = 'process_pool'
    custom = 'custom'


class Priority(Enum):
    """Task scheduling priority levels.

    - low: Background tasks, can be delayed
    - normal: Standard priority for most operations
    - high: Time-sensitive operations
    - realtime: Critical operations requiring immediate execution
    """

    low = 'low'
    normal = 'normal'
    high = 'high'
    realtime = 'realtime'


class SchedulingSpec(ExtensionModel):
    executor: Executor | None = Field(None, description='Where this runs')
    priority: Priority | None = Field(None, description='Scheduling priority')
    preemptible: bool | None = Field(
        None, description='Whether execution can be preempted'
    )
    timeout: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Default timeout in seconds'
    )


class AsyncMethodFields(ExtensionModel):
    async_: bool | None = Field(
        False, alias='async', description='Whether this is an async method'
    )
    awaitable: bool | None = Field(
        None, description='Whether the return value is awaitable'
    )
    blocking: bool | None = Field(
        None, description='Whether this method blocks the event loop'
    )
    cancellation: CancellationSpec | None = None


class AsyncFunctionFields(ExtensionModel):
    async_: bool | None = Field(
        False, alias='async', description='Whether this is an async function'
    )
    awaitable: bool | None = Field(
        None, description='Whether the return value is awaitable'
    )
    blocking: bool | None = Field(
        None, description='Whether this function blocks the event loop'
    )
    cancellation: CancellationSpec | None = None


class LifecycleSpec(ExtensionModel):
    states: list[AsyncStateSpec] | None = Field(None, description='All possible states')
    initial_state: str | None = Field(None, description='Initial state name')
    transitions: list[AsyncTransitionSpec] | None = Field(
        None, description='Valid state transitions'
    )


class AsyncTypeFields(ExtensionModel):
    lifecycle: LifecycleSpec | None = None
    synchronization: SyncSpec | None = None
    observable: ObservableSpec | None = None
    scheduling: SchedulingSpec | None = None
