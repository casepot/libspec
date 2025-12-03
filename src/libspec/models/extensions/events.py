"""Events extension models for libspec specifications.

This module defines models for event-driven architecture:
- Event types and payloads
- Event handlers and listeners
- Event bus and message queue patterns
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import (
    FunctionReference,
    NonEmptyStr,
    RegexPattern,
    SemVer,
    TimeWindow,
    TopicName,
)


class EventsTypeFields(ExtensionModel):
    emits: list[str] | None = Field(None, description='Events this type emits')
    handles: list[str] | None = Field(None, description='Events this type handles')
    domain_events: bool | None = Field(
        None, description='Whether this is a domain event aggregate'
    )


class EventsMethodFields(ExtensionModel):
    emits: list[str] | None = Field(None, description='Events this method emits')
    triggers_on: list[str] | None = Field(
        None, description='Events that trigger this method'
    )


class EventCategory(str, Enum):
    """Category of event for routing and handling.

    - domain: Core business domain events
    - integration: Cross-system integration events
    - notification: User-facing notifications
    - system: Infrastructure/operational events
    - command: Request to perform an action
    - query: Request for information
    """

    domain = 'domain'
    integration = 'integration'
    notification = 'notification'
    system = 'system'
    command = 'command'
    query = 'query'


class EventFieldSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Field name')
    type: str = Field(default=..., description='Field type')
    required: bool | None = Field(True, description='Whether field is required')
    description: str | None = None


class Ordering(str, Enum):
    """Event ordering guarantee for handlers.

    - none: No ordering guarantee
    - fifo: First-in, first-out global ordering
    - partition_fifo: FIFO within partition key
    """

    none = 'none'
    fifo = 'fifo'
    partition_fifo = 'partition_fifo'


class Backoff(str, Enum):
    """Retry backoff strategy for failed operations.

    - fixed: Same delay between retries
    - exponential: Delay doubles each retry
    - linear: Delay increases by fixed amount
    - fibonacci: Delay follows Fibonacci sequence
    """

    fixed = 'fixed'
    exponential = 'exponential'
    linear = 'linear'
    fibonacci = 'fibonacci'


class RetrySpec(ExtensionModel):
    max_attempts: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Maximum retry attempts'
    )
    backoff: Backoff | None = Field(None, description='Backoff strategy')
    initial_delay: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Initial delay in seconds'
    )
    max_delay: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Maximum delay in seconds'
    )
    jitter: bool | None = Field(None, description='Whether to add jitter')
    retryable_exceptions: list[str] | None = Field(
        None, description='Exceptions that trigger retry'
    )

    @model_validator(mode='after')
    def validate_retry_config(self) -> 'RetrySpec':
        """Validate retry configuration completeness."""
        import warnings

        if self.backoff is not None and self.initial_delay is None:
            warnings.warn(
                "backoff strategy specified without initial_delay",
                UserWarning,
                stacklevel=2,
            )
        if self.initial_delay is not None and self.max_delay is not None:
            if self.max_delay < self.initial_delay:
                raise ValueError(
                    f"max_delay ({self.max_delay}) must be >= initial_delay ({self.initial_delay})"
                )
        return self


class Operator(str, Enum):
    """Comparison operators for event filtering.

    Standard comparison and pattern matching operators.
    """

    eq = 'eq'
    neq = 'neq'
    gt = 'gt'
    gte = 'gte'
    lt = 'lt'
    lte = 'lte'
    in_ = 'in'
    contains = 'contains'
    regex = 'regex'


class EventFilterSpec(ExtensionModel):
    field: str | None = Field(None, description='Field to filter on')
    operator: Operator | None = Field(None, description='Filter operator')
    value: Any | None = Field(None, description='Filter value')
    description: str | None = None


class EventBusType(str, Enum):
    """Event bus/message broker implementation.

    - in_memory: Local in-process event bus
    - redis: Redis Pub/Sub or Streams
    - rabbitmq: RabbitMQ/AMQP
    - kafka: Apache Kafka
    - sqs: AWS SQS
    - pubsub: Google Cloud Pub/Sub
    - nats: NATS messaging
    - custom: Custom implementation
    """

    in_memory = 'in_memory'
    redis = 'redis'
    rabbitmq = 'rabbitmq'
    kafka = 'kafka'
    sqs = 'sqs'
    pubsub = 'pubsub'
    nats = 'nats'
    custom = 'custom'


class OrderingGuarantee(str, Enum):
    """Message ordering guarantee level.

    - none: No ordering guarantees
    - per_partition: Ordering within partition key
    - global_: Total ordering across all messages
    """

    none = 'none'
    per_partition = 'per_partition'
    global_ = 'global'


class EventBusSpec(ExtensionModel):
    type: EventBusType | None = Field(None, description='Event bus type')
    async_dispatch: bool | None = Field(None, description='Whether dispatch is async')
    guaranteed_delivery: bool | None = Field(
        None, description='Whether delivery is guaranteed'
    )
    ordering_guarantee: OrderingGuarantee | None = Field(
        None, description='Ordering guarantee level'
    )
    at_least_once: bool | None = Field(None, description='At-least-once delivery')
    at_most_once: bool | None = Field(None, description='At-most-once delivery')
    exactly_once: bool | None = Field(None, description='Exactly-once delivery')
    transactional_outbox: bool | None = Field(
        None, description='Whether transactional outbox pattern is supported'
    )
    event_sourcing: bool | None = Field(
        None, description='Whether event sourcing is supported'
    )

    @model_validator(mode='after')
    def validate_delivery_guarantees(self) -> 'EventBusSpec':
        """Validate delivery guarantees are mutually exclusive."""
        guarantees = [
            ('at_least_once', self.at_least_once),
            ('at_most_once', self.at_most_once),
            ('exactly_once', self.exactly_once),
        ]
        active = [name for name, value in guarantees if value is True]
        if len(active) > 1:
            raise ValueError(
                f"Delivery guarantees are mutually exclusive, got: {', '.join(active)}"
            )
        return self


class TopicSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Topic name')
    pattern: RegexPattern | None = Field(None, description='Topic pattern (for wildcards)')
    partitions: Annotated[int, Field(ge=1)] | None = Field(default=None, description='Number of partitions')
    retention: TimeWindow | None = Field(None, description='Message retention period')
    events: list[str] | None = Field(
        None, description='Event types published to this topic'
    )
    subscribers: list[str] | None = Field(None, description='Subscriber handler names')
    description: str | None = None


class Persistence(str, Enum):
    """Where saga/process state is persisted.

    - in_memory: No persistence (lost on restart)
    - database: Traditional database storage
    - event_store: Event sourcing storage
    """

    in_memory = 'in_memory'
    database = 'database'
    event_store = 'event_store'


class OnFailure(str, Enum):
    """How saga steps handle failures.

    - compensate: Run compensation actions
    - retry: Retry the failed step
    - skip: Skip and continue to next step
    - abort: Abort the entire saga
    """

    compensate = 'compensate'
    retry = 'retry'
    skip = 'skip'
    abort = 'abort'


class SagaStepSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Step name')
    action: str | None = Field(None, description='Action to perform (command/event)')
    wait_for: list[str] | None = Field(None, description='Events to wait for')
    timeout: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Step timeout in seconds'
    )
    on_failure: OnFailure | None = Field(None, description='Failure handling')


class CompensationSpec(ExtensionModel):
    step: str = Field(default=..., description='Step to compensate')
    action: str = Field(default=..., description='Compensation action')
    idempotent: bool | None = Field(
        None, description='Whether compensation is idempotent'
    )


class EventSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Event type name')
    type: str | None = Field(None, description='Event class reference')
    category: EventCategory | None = Field(None, description='Event category')
    payload: list[EventFieldSpec] | None = Field(
        None, description='Event payload fields'
    )
    metadata: list[EventFieldSpec] | None = Field(
        None, description='Standard metadata fields'
    )
    topic: TopicName | None = Field(None, description='Default topic/channel')
    version: SemVer | None = Field(None, description='Event schema version')
    idempotency_key: str | None = Field(None, description='Field used for idempotency')
    ordering_key: str | None = Field(None, description='Field used for ordering')
    ttl: TimeWindow | None = Field(None, description='Event time-to-live')
    description: str | None = None


class HandlerSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Handler name')
    handles: list[str] | None = Field(None, description='Events this handler processes')
    function: FunctionReference | None = Field(None, description='Handler function reference')
    async_: bool | None = Field(
        None, alias='async', description='Whether handler is async'
    )
    retry: RetrySpec | None = None
    timeout: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Handler timeout in seconds'
    )
    concurrency: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Max concurrent executions'
    )
    ordering: Ordering | None = Field(None, description='Event ordering guarantee')
    idempotent: bool | None = Field(None, description='Whether handler is idempotent')
    dead_letter: TopicName | None = Field(None, description='Dead letter topic on failure')
    filters: list[EventFilterSpec] | None = Field(None, description='Event filters')
    description: str | None = None

    @model_validator(mode='after')
    def validate_handles_not_empty(self) -> 'HandlerSpec':
        """Validate handles list is not empty when provided."""
        if self.handles is not None and len(self.handles) == 0:
            raise ValueError(
                f"Handler '{self.name}' has empty handles list; "
                "either omit handles or specify at least one event"
            )
        return self


class SagaSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Saga name')
    type: str | None = Field(None, description='Saga class reference')
    starts_with: list[str] | None = Field(
        None, description='Events that start this saga'
    )
    steps: list[SagaStepSpec] | None = Field(None, description='Saga steps')
    compensations: list[CompensationSpec] | None = Field(
        None, description='Compensation actions'
    )
    timeout: Annotated[float, Field(ge=0.0)] | None = Field(
        default=None, description='Saga timeout in seconds'
    )
    persistence: Persistence | None = Field(
        None, description='State persistence strategy'
    )
    description: str | None = None


class EventsLibraryFields(ExtensionModel):
    events: list[EventSpec] | None = Field(None, description='Event type definitions')
    handlers: list[HandlerSpec] | None = Field(
        None, description='Event handler definitions'
    )
    event_bus: EventBusSpec | None = None
    topics: list[TopicSpec] | None = Field(
        None, description='Topic/channel definitions'
    )
    sagas: list[SagaSpec] | None = Field(
        None, description='Saga/process manager definitions'
    )
