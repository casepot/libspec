"""Data extension models for libspec specifications.

This module defines models for data processing and transformation:
- Serialization and validation
- Schema definitions and formats
- Data transformation pipelines
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import Field

from libspec.models.base import ExtensionModel
from libspec.models.types import NonEmptyStr, TypeAnnotationStr


class CopySemantics(str, Enum):
    """Data copy behavior for operations.

    - copy: Always create a deep copy
    - view: Return a view (shares underlying data)
    - copy_on_write: Copy only when modified
    - configurable: User can choose per-operation
    """

    copy = 'copy'
    view = 'view'
    copy_on_write = 'copy_on_write'
    configurable = 'configurable'


class DTypeCategory(str, Enum):
    """Data type category for classification.

    - numeric: Integer, float, decimal types
    - string: Text/string types
    - temporal: Date, time, datetime types
    - boolean: True/false type
    - categorical: Enum-like categorical type
    - nested: Struct, list, map types
    - binary: Raw binary/bytes type
    - null: Null/missing value type
    - custom: Custom user-defined type
    """

    numeric = 'numeric'
    string = 'string'
    temporal = 'temporal'
    boolean = 'boolean'
    categorical = 'categorical'
    nested = 'nested'
    binary = 'binary'
    null = 'null'
    custom = 'custom'


class DTypeSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Data type name')
    category: DTypeCategory | None = Field(None, description='Type category')
    numpy_equivalent: str | None = Field(None, description='Equivalent NumPy dtype')
    python_type: TypeAnnotationStr | None = Field(
        None, description='Python type for scalar values'
    )
    nullable: bool | None = Field(None, description='Whether null values are supported')
    bit_width: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Bit width (for numeric types)'
    )
    signed: bool | None = Field(None, description='Whether signed (for integer types)')
    precision: str | None = Field(
        None, description='Precision (for temporal/decimal types)'
    )
    description: str | None = None


class Behavior(str, Enum):
    """Type coercion behavior.

    - implicit: Automatically convert types
    - explicit: Require explicit cast call
    - error: Raise error on type mismatch
    - warning: Warn but allow conversion
    """

    implicit = 'implicit'
    explicit = 'explicit'
    error = 'error'
    warning = 'warning'


class CoercionRule(ExtensionModel):
    from_: str | None = Field(None, alias='from', description='Source type')
    to: str | None = Field(None, description='Target type')
    behavior: Behavior | None = Field(None, description='What happens during coercion')
    lossy: bool | None = Field(
        None, description='Whether conversion may lose information'
    )


class TransformCategory(str, Enum):
    """Data transformation operation category.

    - select: Column/field selection
    - filter: Row/record filtering
    - aggregate: Grouping and aggregation
    - join: Combining datasets
    - reshape: Pivot, melt, stack operations
    - sort: Ordering records
    - window: Window/rolling operations
    - fill: Missing value handling
    - cast: Type conversion
    - custom: Custom transformation
    """

    select = 'select'
    filter = 'filter'
    aggregate = 'aggregate'
    join = 'join'
    reshape = 'reshape'
    sort = 'sort'
    window = 'window'
    fill = 'fill'
    cast = 'cast'
    custom = 'custom'


class TransformSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Transform name')
    category: TransformCategory = Field(default=..., description='Transform category')
    method: str | None = Field(None, description='Method reference')
    input_shape: str | None = Field(
        None, description="Expected input shape (e.g., '1D', '2D', 'any')"
    )
    output_shape: str | None = Field(None, description='Resulting output shape')
    preserves_order: bool | None = Field(
        None, description='Whether row order is preserved'
    )
    preserves_index: bool | None = Field(None, description='Whether index is preserved')
    description: str | None = None


class MethodChainingSpec(ExtensionModel):
    fluent_api: bool | None = Field(
        None, description='Whether methods return self for chaining'
    )
    immutable_chain: bool | None = Field(
        None, description='Whether each chain step creates new instance'
    )
    chainable_methods: list[str] | None = Field(
        None, description='Methods that support chaining'
    )
    terminal_methods: list[str] | None = Field(
        None, description='Methods that break the chain (return different type)'
    )


class PipelineType(str, Enum):
    """Data pipeline execution model.

    - sequential: Linear step-by-step execution
    - dag: Directed acyclic graph (parallel branches)
    - streaming: Continuous data flow
    - batch: Batch processing
    """

    sequential = 'sequential'
    dag = 'dag'
    streaming = 'streaming'
    batch = 'batch'


class ErrorHandling(str, Enum):
    """Pipeline error handling strategy.

    - fail_fast: Stop on first error
    - collect: Collect all errors, report at end
    - skip: Skip failed records, continue
    - retry: Retry failed operations
    """

    fail_fast = 'fail_fast'
    collect = 'collect'
    skip = 'skip'
    retry = 'retry'


class PipelineStage(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Stage name')
    transform: str | None = Field(None, description='Transform to apply')
    inputs: list[str] | None = Field(None, description='Input names (for DAG)')
    output: str | None = Field(None, description='Output name')
    optional: bool | None = Field(None, description='Whether stage can be skipped')


class IOFormatSpec(ExtensionModel):
    format: str = Field(default=..., description="Format name (e.g., 'csv', 'parquet', 'json')")
    read_method: str | None = Field(None, description='Method for reading this format')
    write_method: str | None = Field(None, description='Method for writing this format')
    streaming: bool | None = Field(
        None, description='Whether streaming read/write is supported'
    )
    compression: list[str] | None = Field(
        None, description='Supported compression codecs'
    )
    schema_support: bool | None = Field(
        None, description='Whether format supports schema'
    )
    partitioning: bool | None = Field(
        None, description='Whether partitioned read/write is supported'
    )


class Default(str, Enum):
    """Default evaluation strategy.

    - eager: Evaluate operations immediately
    - lazy: Defer evaluation until needed
    - configurable: User can choose
    """

    eager = 'eager'
    lazy = 'lazy'
    configurable = 'configurable'


class EvaluationStrategySpec(ExtensionModel):
    default: Default | None = Field(None, description='Default evaluation strategy')
    lazy_operations: list[str] | None = Field(
        None, description='Operations that are always lazy'
    )
    eager_triggers: list[str] | None = Field(
        None, description='Operations that trigger evaluation'
    )
    collect_method: str | None = Field(
        None, description='Method to trigger full evaluation'
    )
    streaming_collect: bool | None = Field(
        None, description='Whether streaming evaluation is supported'
    )
    query_optimization: bool | None = Field(
        None, description='Whether query optimization is performed'
    )
    explain_method: str | None = Field(None, description='Method to explain query plan')


class Layout(str, Enum):
    """Memory layout for data storage.

    - row_major: Row-contiguous (C-style)
    - column_major: Column-contiguous (Fortran-style)
    - chunked: Data stored in chunks
    - arrow: Apache Arrow format
    - custom: Custom layout
    """

    row_major = 'row_major'
    column_major = 'column_major'
    chunked = 'chunked'
    arrow = 'arrow'
    custom = 'custom'


class StringStorage(str, Enum):
    """String data storage strategy.

    - utf8: Standard UTF-8 encoding
    - large_utf8: Large string type (64-bit offsets)
    - dictionary: Dictionary-encoded strings
    - fixed_size: Fixed-size string buffer
    """

    utf8 = 'utf8'
    large_utf8 = 'large_utf8'
    dictionary = 'dictionary'
    fixed_size = 'fixed_size'


class MemoryLayoutSpec(ExtensionModel):
    layout: Layout | None = Field(None, description='Memory layout')
    contiguous: bool | None = Field(
        None, description='Whether data is stored contiguously'
    )
    zero_copy: bool | None = Field(
        None, description='Whether zero-copy operations are supported'
    )
    memory_mapped: bool | None = Field(
        None, description='Whether memory mapping is supported'
    )
    string_storage: StringStorage | None = Field(
        None, description='String storage strategy'
    )


class Backend(str, Enum):
    """Parallelism execution backend.

    - threads: ThreadPoolExecutor
    - processes: ProcessPoolExecutor
    - dask: Dask distributed computing
    - ray: Ray distributed computing
    - spark: Apache Spark
    - none: No parallelism
    """

    threads = 'threads'
    processes = 'processes'
    dask = 'dask'
    ray = 'ray'
    spark = 'spark'
    none = 'none'


class ParallelismSpec(ExtensionModel):
    backend: Backend | None = Field(None, description='Parallelism backend')
    default_threads: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Default thread count'
    )
    auto_parallel: bool | None = Field(
        None, description='Whether operations auto-parallelize'
    )
    min_size_for_parallel: Annotated[int, Field(ge=0)] | None = Field(
        default=None, description='Minimum data size for parallel execution'
    )
    parallel_operations: list[str] | None = Field(
        None, description='Operations that support parallelism'
    )


class BroadcastingSpec(ExtensionModel):
    supported: bool | None = Field(
        None, description='Whether broadcasting is supported'
    )
    rules: str | None = Field(
        None, description="Broadcasting rules (e.g., 'numpy', 'strict')"
    )
    scalar_expansion: bool | None = Field(
        None, description='Whether scalars are expanded'
    )


class Rules(str, Enum):
    """Type promotion rule set.

    - numpy: NumPy-style type promotion
    - pandas: Pandas-style type promotion
    - strict: No automatic promotion
    - custom: Custom promotion rules
    """

    numpy = 'numpy'
    pandas = 'pandas'
    strict = 'strict'
    custom = 'custom'


class OverflowBehavior(str, Enum):
    """Numeric overflow handling behavior.

    - wrap: Wrap around (modular arithmetic)
    - saturate: Clamp to min/max value
    - error: Raise exception on overflow
    - promote: Promote to larger type
    """

    wrap = 'wrap'
    saturate = 'saturate'
    error = 'error'
    promote = 'promote'


class DTypePromotionSpec(ExtensionModel):
    rules: Rules | None = Field(None, description='Promotion rule set')
    result_dtype: str | None = Field(
        None, description='Result dtype for this operation'
    )
    overflow_behavior: OverflowBehavior | None = Field(
        None, description='Behavior on overflow'
    )


class DataMethodFields(ExtensionModel):
    lazy: bool | None = Field(
        None, description='Whether this method is lazily evaluated'
    )
    in_place: bool | None = Field(
        None, description='Whether this method modifies data in place'
    )
    copy_semantics: CopySemantics | None = Field(None, description='Copy behavior')
    broadcasting: BroadcastingSpec | None = None
    dtype_promotion: DTypePromotionSpec | None = None
    parallelizable: bool | None = Field(
        None, description='Whether this operation can be parallelized'
    )
    chunked: bool | None = Field(
        None, description='Whether this operation supports chunked processing'
    )


class DTypeBehaviorSpec(ExtensionModel):
    supported_dtypes: list[str] | None = Field(None, description='Supported data types')
    default_dtype: str | None = Field(
        None, description='Default dtype when not specified'
    )
    dtype_inference: bool | None = Field(
        None, description='Whether dtype is inferred automatically'
    )
    strict_typing: bool | None = Field(
        None, description='Whether type mismatches raise errors'
    )
    coercion_rules: list[CoercionRule] | None = Field(
        None, description='Type coercion rules'
    )


class PipelineSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Pipeline name')
    type: PipelineType | None = Field(None, description='Pipeline type')
    stages: list[PipelineStage] | None = Field(None, description='Pipeline stages')
    error_handling: ErrorHandling | None = Field(
        None, description='How errors are handled'
    )
    checkpointing: bool | None = Field(
        None, description='Whether checkpointing is supported'
    )
    description: str | None = None


class DataLibraryFields(ExtensionModel):
    dtypes: list[DTypeSpec] | None = Field(
        None, description='Data types supported by the library'
    )
    transforms: list[TransformSpec] | None = Field(
        None, description='Data transformation operations'
    )
    pipelines: list[PipelineSpec] | None = Field(
        None, description='Pipeline/workflow definitions'
    )
    io_formats: list[IOFormatSpec] | None = Field(
        None, description='Supported I/O formats'
    )
    evaluation_strategy: EvaluationStrategySpec | None = None


class DataTypeFields(ExtensionModel):
    dtype_behavior: DTypeBehaviorSpec | None = None
    method_chaining: MethodChainingSpec | None = None
    memory_layout: MemoryLayoutSpec | None = None
    parallelism: ParallelismSpec | None = None
