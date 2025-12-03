"""Performance extension models for libspec specifications.

This module defines models for performance specifications:
- Time complexity and benchmarks
- Memory usage and constraints
- Caching strategies and optimizations
"""

from __future__ import annotations

from datetime import date as date_aliased
from decimal import Decimal
from typing import Annotated

from pydantic import Field

from libspec.models.base import ExtensionModel


class ComplexitySpec(ExtensionModel):
    time: str | None = Field(None, description="Time complexity (e.g., 'O(n log n)')")
    space: str | None = Field(None, description="Space complexity (e.g., 'O(n)')")
    best_case: str | None = Field(None, description='Best-case time complexity')
    worst_case: str | None = Field(None, description='Worst-case time complexity')
    amortized: str | None = Field(None, description='Amortized time complexity')
    notes: str | None = Field(None, description='Additional notes about complexity')


class BenchmarkSpec(ExtensionModel):
    operation: str | None = Field(None, description='What was benchmarked')
    input_size: str | None = Field(None, description='Input size/parameters')
    mean: Annotated[Decimal, Field(gt=0)] | None = Field(default=None, description='Mean execution time')
    median: Annotated[Decimal, Field(gt=0)] | None = Field(default=None, description='Median execution time')
    p95: Annotated[Decimal, Field(gt=0)] | None = Field(default=None, description='95th percentile latency')
    p99: Annotated[Decimal, Field(gt=0)] | None = Field(default=None, description='99th percentile latency')
    memory_peak: Annotated[Decimal, Field(gt=0)] | None = Field(default=None, description='Peak memory usage')
    throughput: Annotated[Decimal, Field(gt=0)] | None = Field(
        default=None, description='Operations per second'
    )
    environment: str | None = Field(None, description='Hardware/software environment')
    date: date_aliased | None = Field(None, description='When benchmark was run')


class MemoryLayoutSpec(ExtensionModel):
    size_bytes: Annotated[int, Field(ge=0)] | None = Field(default=None, description='Instance size in bytes')
    alignment: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Memory alignment requirement'
    )
    cache_friendly: bool | None = Field(
        None, description='Whether layout is cache-optimized'
    )
    slots: bool | None = Field(None, description='Whether __slots__ is used')


class ScalingSpec(ExtensionModel):
    horizontal: bool | None = Field(None, description='Supports horizontal scaling')
    vertical: bool | None = Field(None, description='Supports vertical scaling')
    bottleneck: str | None = Field(None, description='Primary scaling bottleneck')
    max_concurrent: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Maximum concurrent operations'
    )
    sharding_supported: bool | None = Field(
        None, description='Whether sharding is supported'
    )


class PerfMethodFields(ExtensionModel):
    complexity: ComplexitySpec | None = None
    benchmarks: list[BenchmarkSpec] | None = None
    optimization_hints: list[str] | None = Field(
        None, description='Tips for optimal usage'
    )


class PerfFunctionFields(ExtensionModel):
    complexity: ComplexitySpec | None = None
    benchmarks: list[BenchmarkSpec] | None = None
    optimization_hints: list[str] | None = Field(
        None, description='Tips for optimal usage'
    )


class PerfTypeFields(ExtensionModel):
    memory_layout: MemoryLayoutSpec | None = None
    scaling: ScalingSpec | None = None
