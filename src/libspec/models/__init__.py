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
    EnumValue,
    Feature,
    FunctionDef,
    GenericParam,
    Library,
    LibspecSpec,
    Method,
    Module,
    Parameter,
    Principle,
    Property,
    RaisesClause,
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
    EvidenceBase,
    EvidenceSpec,
    EvidenceTypeSpec,
    EventsLibraryFields,
    EventsMethodFields,
    EventsTypeFields,
    GateSpec,
    LifecycleFields,
    LifecycleLibraryFields,
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
    TestsEvidence,
    TestingLibraryFields,
    TestingTypeFields,
    VersioningLibraryFields,
    VersioningMethodFields,
    VersioningTypeFields,
    WebLibraryFields,
    WorkflowSpec,
)
from .types import (
    ExtensionName,
    FeatureStatus,
    FunctionKind,
    GenericVariance,
    KebabCaseId,
    LibraryName,
    ModulePath,
    ParameterKind,
    PascalCaseName,
    SchemaVersion,
    ScreamingSnakeCase,
    SemVer,
    SnakeCaseId,
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
    # Enums
    "TypeKind",
    "FunctionKind",
    "ParameterKind",
    "FeatureStatus",
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
    # Lifecycle extension types
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
    "EvidenceTypeSpec",
    "WorkflowSpec",
    "LifecycleFields",
    "LifecycleLibraryFields",
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
