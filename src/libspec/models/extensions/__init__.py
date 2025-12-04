"""Extension models for libspec.

Each extension adds optional fields to core entity types.
"""

from .async_ import AsyncFunctionFields, AsyncMethodFields, AsyncTypeFields
from .cli import CLILibraryFields
from .config import ConfigLibraryFields
from .data import DataLibraryFields, DataMethodFields, DataTypeFields
from .errors import ErrorsLibraryFields
from .events import EventsLibraryFields, EventsMethodFields, EventsTypeFields
from .lifecycle import (
    ApprovalEvidence,
    BenchmarkEvidence,
    CustomEvidence,
    DeprecationNoticeEvidence,
    DesignDocEvidence,
    DevStateSpec,
    DevTransitionSpec,
    DocsEvidence,
    EvidenceBase,
    EvidenceSpec,
    EvidenceTypeSpec,
    GateSpec,
    LifecycleFields,
    LifecycleLibraryFields,
    MaturityGate,
    MigrationGuideEvidence,
    PrEvidence,
    TestsEvidence,
    WorkflowSpec,
)
from .observability import ObservabilityLibraryFields
from .orm import ORMLibraryFields
from .perf import PerfFunctionFields, PerfMethodFields, PerfTypeFields
from .plugins import PluginsLibraryFields, PluginsTypeFields
from .safety import SafetyFunctionFields, SafetyMethodFields, SafetyTypeFields
from .serialization import (
    SerializationFunctionFields,
    SerializationLibraryFields,
    SerializationMethodFields,
    SerializationTypeFields,
)
from .state import StateLibraryFields, StateTypeFields
from .testing import TestingLibraryFields, TestingTypeFields
from .versioning import (
    VersioningLibraryFields,
    VersioningMethodFields,
    VersioningTypeFields,
)
from .web import WebLibraryFields

__all__ = [
    # Lifecycle evidence and workflow types
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
    # Serialization
    "SerializationLibraryFields",
    "SerializationTypeFields",
    "SerializationMethodFields",
    "SerializationFunctionFields",
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
