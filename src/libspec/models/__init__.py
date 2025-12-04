"""Pydantic models for libspec specifications.

This package provides strongly-typed models for library specifications,
replacing the JSON Schema + TypedDict approach with a Pydantic-first
architecture where models are the source of truth.

Usage:
    from libspec.models import LibspecSpec, Library, TypeDef

    # Parse a spec file
    spec = LibspecSpec.model_validate(data)

    # Access typed properties
    for t in spec.library.types:
        print(f"{t.name}: {t.kind}")
"""

from .base import ExtensibleModel, ExtensionModel, LibspecModel
from .core import (
    Constructor,
    DeprecationInfo,
    EnumValue,
    Export,
    Feature,
    FunctionDef,
    GenericParam,
    Library,
    LibspecSpec,
    Method,
    Module,
    OverloadSpec,
    Parameter,
    Principle,
    Property,
    RaisesClause,
    Requirement,
    ReturnSpec,
    TypeDef,
    YieldSpec,
)
from .extensions import (
    ApprovalEvidence,
    AsyncFunctionFields,
    AsyncMethodFields,
    AsyncTypeFields,
    BenchmarkEvidence,
    CLILibraryFields,
    ConfigLibraryFields,
    CustomEvidence,
    DataLibraryFields,
    DataMethodFields,
    DataTypeFields,
    DeprecationNoticeEvidence,
    DesignDocEvidence,
    DevStateSpec,
    DevTransitionSpec,
    DocsEvidence,
    ErrorsLibraryFields,
    EventsLibraryFields,
    EventsMethodFields,
    EventsTypeFields,
    EvidenceBase,
    EvidenceSpec,
    EvidenceTypeSpec,
    GateSpec,
    WorkflowFields,
    WorkflowLibraryFields,
    MaturityGate,
    MigrationGuideEvidence,
    ObservabilityLibraryFields,
    ORMLibraryFields,
    PerfFunctionFields,
    PerfMethodFields,
    PerfTypeFields,
    PluginsLibraryFields,
    PluginsTypeFields,
    PrEvidence,
    SafetyFunctionFields,
    SafetyMethodFields,
    SafetyTypeFields,
    StateLibraryFields,
    StateTypeFields,
    TestingLibraryFields,
    TestingTypeFields,
    TestsEvidence,
    VersioningLibraryFields,
    VersioningMethodFields,
    VersioningTypeFields,
    WebLibraryFields,
    WorkflowSpec,
)
from .types import (
    # Numeric constrained types
    ByteSize,
    CommandName,
    ConfigKey,
    EntityMaturity,
    ExceptionTypeName,
    ExecutionOrder,
    ExtensionName,
    FeatureStatus,
    FormatName,
    FinitePositiveDecimal,
    FunctionKind,
    GenericVariance,
    HttpStatusCode,
    IntervalSeconds,
    KebabCaseId,
    LibraryName,
    ModulePath,
    NonNegativeFloat,
    NonNegativeInt,
    ParameterKind,
    PascalCaseName,
    Percentage,
    PositiveFloat,
    PositiveInt,
    Priority,
    SamplingRate,
    SchemaVersion,
    ScreamingSnakeCase,
    SemVer,
    SnakeCaseId,
    StateName,
    TimeoutSeconds,
    TypeKind,
)

__all__ = [
    # Base classes
    "LibspecModel",
    "ExtensibleModel",
    "ExtensionModel",
    # Root containers
    "LibspecSpec",
    "Library",
    # Entity types
    "TypeDef",
    "FunctionDef",
    "Feature",
    "Module",
    "Principle",
    # Type members
    "Method",
    "Constructor",
    "Property",
    "EnumValue",
    "GenericParam",
    # Function components
    "Parameter",
    "ReturnSpec",
    "YieldSpec",
    "RaisesClause",
    "OverloadSpec",
    "DeprecationInfo",
    # Dependency tracking
    "Requirement",
    # Module components
    "Export",
    # Enums
    "TypeKind",
    "FunctionKind",
    "ParameterKind",
    "FeatureStatus",
    "EntityMaturity",
    "GenericVariance",
    "ExtensionName",
    # Constrained types
    "KebabCaseId",
    "SnakeCaseId",
    "PascalCaseName",
    "ScreamingSnakeCase",
    "LibraryName",
    "SemVer",
    "SchemaVersion",
    "ModulePath",
    # Numeric constrained types
    "HttpStatusCode",
    "ExecutionOrder",
    "Priority",
    "SamplingRate",
    "Percentage",
    "TimeoutSeconds",
    "IntervalSeconds",
    "PositiveInt",
    "NonNegativeInt",
    "PositiveFloat",
    "NonNegativeFloat",
    "FinitePositiveDecimal",
    "ByteSize",
    # Semantic string types
    "StateName",
    "CommandName",
    "FormatName",
    "ConfigKey",
    "ExceptionTypeName",
    # Workflow extension types
    "EvidenceBase",
    "EvidenceSpec",
    "PrEvidence",
    "TestsEvidence",
    "DesignDocEvidence",
    "DocsEvidence",
    "ApprovalEvidence",
    "BenchmarkEvidence",
    "MigrationGuideEvidence",
    "DeprecationNoticeEvidence",
    "CustomEvidence",
    "GateSpec",
    "DevStateSpec",
    "DevTransitionSpec",
    "MaturityGate",
    "EvidenceTypeSpec",
    "WorkflowSpec",
    "WorkflowFields",
    "WorkflowLibraryFields",
    # Async
    "AsyncMethodFields",
    "AsyncFunctionFields",
    "AsyncTypeFields",
    # CLI
    "CLILibraryFields",
    # Config
    "ConfigLibraryFields",
    # Data
    "DataLibraryFields",
    "DataMethodFields",
    "DataTypeFields",
    # Errors
    "ErrorsLibraryFields",
    # Events
    "EventsLibraryFields",
    "EventsMethodFields",
    "EventsTypeFields",
    # Observability
    "ObservabilityLibraryFields",
    # ORM
    "ORMLibraryFields",
    # Performance
    "PerfFunctionFields",
    "PerfMethodFields",
    "PerfTypeFields",
    # Plugins
    "PluginsLibraryFields",
    "PluginsTypeFields",
    # Safety
    "SafetyFunctionFields",
    "SafetyMethodFields",
    "SafetyTypeFields",
    # State
    "StateLibraryFields",
    "StateTypeFields",
    # Testing
    "TestingLibraryFields",
    "TestingTypeFields",
    # Versioning
    "VersioningLibraryFields",
    "VersioningMethodFields",
    "VersioningTypeFields",
    # Web
    "WebLibraryFields",
]
