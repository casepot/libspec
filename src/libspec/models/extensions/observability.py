"""Observability extension models for libspec specifications.

This module defines models for observability specifications:
- Logging configuration and structured logs
- Metrics collection and aggregation
- Distributed tracing and spans
"""

from __future__ import annotations

from enum import Enum

from typing import Annotated

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import MetricName, NonEmptyStr


class LogLevel(str, Enum):
    """Standard Python logging levels."""

    DEBUG = 'DEBUG'
    INFO = 'INFO'
    WARNING = 'WARNING'
    ERROR = 'ERROR'
    CRITICAL = 'CRITICAL'


class LoggingSpec(ExtensionModel):
    logger_name: str | None = Field(None, description="Logger name (e.g., 'mylib')")
    levels_used: list[LogLevel] | None = Field(
        None, description='Log levels used'
    )
    structured: bool | None = Field(
        None, description='Whether structured logging is used'
    )
    context_fields: list[str] | None = Field(
        None, description='Context fields included in log entries'
    )
    sensitive_fields: list[str] | None = Field(
        None, description='Fields that are masked in logs'
    )
    rate_limiting: bool | None = Field(
        None, description='Whether log rate limiting is supported'
    )
    sampling: bool | None = Field(None, description='Whether log sampling is supported')


class MetricType(str, Enum):
    """Prometheus-style metric types.

    - counter: Monotonically increasing value (e.g., request count)
    - gauge: Value that can go up or down (e.g., temperature)
    - histogram: Distribution of values in buckets (e.g., latencies)
    - summary: Distribution with quantiles (e.g., latency percentiles)
    - info: Informational metric with labels only
    """

    counter = 'counter'
    gauge = 'gauge'
    histogram = 'histogram'
    summary = 'summary'
    info = 'info'


class MetricSpec(ExtensionModel):
    name: MetricName = Field(default=..., description="Metric name (e.g., 'mylib_requests_total')")
    type: MetricType = Field(default=..., description='Metric type')
    description: str | None = Field(None, description='What this metric measures')
    labels: list[str] | None = Field(None, description='Label names for this metric')
    unit: str | None = Field(
        None, description="Unit of measurement (e.g., 'seconds', 'bytes')"
    )
    buckets: list[Annotated[float, Field(ge=0.0)]] | None = Field(
        default=None, description='Histogram buckets (for histogram type)'
    )

    @model_validator(mode='after')
    def validate_histogram_buckets(self) -> 'MetricSpec':
        """If type=histogram, buckets is required and must be sorted."""
        if self.type == MetricType.histogram:
            if self.buckets is None or len(self.buckets) == 0:
                raise ValueError('buckets is required when type=histogram')
            if self.buckets != sorted(self.buckets):
                raise ValueError('buckets must be sorted in ascending order')
        return self


class Propagation(str, Enum):
    """Distributed tracing context propagation format.

    - w3c: W3C Trace Context (standard)
    - b3: Zipkin B3 format
    - jaeger: Jaeger native format
    - xray: AWS X-Ray format
    - datadog: Datadog APM format
    - custom: Custom propagation implementation
    """

    w3c = 'w3c'
    b3 = 'b3'
    jaeger = 'jaeger'
    xray = 'xray'
    datadog = 'datadog'
    custom = 'custom'


class Sampling(str, Enum):
    """Trace sampling strategy.

    - always: Sample every trace
    - never: Never sample (disable tracing)
    - probabilistic: Sample based on probability (e.g., 10%)
    - rate_limited: Sample up to N traces per second
    - parent_based: Follow parent span's sampling decision
    """

    always = 'always'
    never = 'never'
    probabilistic = 'probabilistic'
    rate_limited = 'rate_limited'
    parent_based = 'parent_based'


class TracingSpec(ExtensionModel):
    span_names: list[str] | None = Field(None, description='Span names used')
    propagation: Propagation | None = Field(
        None, description='Context propagation format'
    )
    sampling: Sampling | None = Field(None, description='Sampling strategy')
    sampling_rate: Annotated[float, Field(ge=0.0, le=1.0)] | None = Field(
        default=None, description='Sampling rate (0.0-1.0)'
    )
    attributes: list[str] | None = Field(None, description='Standard span attributes')
    events: list[str] | None = Field(None, description='Span events emitted')
    baggage: list[str] | None = Field(None, description='Baggage items propagated')

    @model_validator(mode='after')
    def validate_sampling_config(self) -> 'TracingSpec':
        """Validate sampling configuration consistency."""
        if self.sampling == Sampling.probabilistic:
            if self.sampling_rate is None:
                raise ValueError('sampling_rate is required when sampling=probabilistic')
        if self.sampling_rate is not None:
            if self.sampling not in (Sampling.probabilistic, Sampling.rate_limited):
                raise ValueError(
                    f"sampling_rate only valid for probabilistic/rate_limited, not {self.sampling}"
                )
        return self


class HealthCheckType(str, Enum):
    """Kubernetes-style health check type.

    - liveness: Is the application alive? Failure triggers restart
    - readiness: Can the application handle traffic? Failure removes from LB
    - startup: Has the application started? Protects slow-starting apps
    """

    liveness = 'liveness'
    readiness = 'readiness'
    startup = 'startup'


class HealthCheckSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Health check name')
    type: HealthCheckType = Field(default=..., description='Health check type')
    endpoint: str | None = Field(None, description='HTTP endpoint path')
    method: str | None = Field(None, description='Method to call for health check')
    timeout: Annotated[float, Field(gt=0)] | None = Field(
        default=None, description='Timeout in seconds'
    )
    interval: Annotated[float, Field(gt=0)] | None = Field(
        default=None, description='Check interval in seconds'
    )
    dependencies: list[str] | None = Field(None, description='Dependencies checked')

    @model_validator(mode='after')
    def validate_timeout_less_than_interval(self) -> 'HealthCheckSpec':
        """Timeout must be less than interval (if both are set)."""
        if self.timeout is not None and self.interval is not None:
            if self.timeout >= self.interval:
                raise ValueError('timeout must be less than interval')
        return self


class TraceFormat(str, Enum):
    """Debug trace output format.

    - json: Machine-readable JSON format
    - text: Plain text format
    - compact: Minimal output format
    - pretty: Human-readable formatted output
    """

    json = 'json'
    text = 'text'
    compact = 'compact'
    pretty = 'pretty'


class DebugToolsSpec(ExtensionModel):
    repr_depth: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Default __repr__ recursion depth'
    )
    sensitive_fields: list[str] | None = Field(
        None, description='Fields redacted in debug output'
    )
    trace_format: TraceFormat | None = Field(None, description='Trace output format')
    profiling_supported: bool | None = Field(
        None, description='Whether profiling hooks are available'
    )
    memory_tracking: bool | None = Field(
        None, description='Whether memory tracking is available'
    )
    async_debug: bool | None = Field(
        None, description='Whether async debugging tools are available'
    )


class ObservabilityLibraryFields(ExtensionModel):
    logging: LoggingSpec | None = None
    metrics: list[MetricSpec] | None = Field(
        None, description='Metrics exposed by the library'
    )
    tracing: TracingSpec | None = None
    health_checks: list[HealthCheckSpec] | None = Field(
        None, description='Health check endpoints'
    )
    debug_tools: DebugToolsSpec | None = None
