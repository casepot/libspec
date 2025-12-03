"""Output models for CLI responses."""

from datetime import datetime, timezone
from typing import Annotated, Any, Generic, TypeVar

from pydantic import BaseModel, Field, PlainSerializer

T = TypeVar("T")


class SpecContext(BaseModel):
    """Metadata about the spec being queried."""

    path: str
    library: str
    version: str


ISODatetime = Annotated[datetime, PlainSerializer(lambda v: v.isoformat(), return_type=str)]


class OutputEnvelope(BaseModel, Generic[T]):
    """Standard envelope for all JSON output."""

    libspec_cli: str = Field(default="0.1.0")
    command: str
    spec: SpecContext
    timestamp: ISODatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: T
    meta: dict[str, Any] = Field(default_factory=dict)


class TypeSummary(BaseModel):
    """Summary of a type definition."""

    name: str
    kind: str
    module: str
    methods_count: int = 0
    properties_count: int = 0
    has_docstring: bool = False
    ref: str


class FunctionSummary(BaseModel):
    """Summary of a function definition."""

    name: str
    kind: str
    module: str
    signature: str
    has_description: bool = False
    ref: str


class FeatureSummary(BaseModel):
    """Summary of a feature specification."""

    id: str
    category: str
    summary: str | None = None
    status: str = "planned"
    steps_count: int = 0
    refs_count: int = 0
    ref: str


class ModuleSummary(BaseModel):
    """Summary of a module."""

    path: str
    description: str | None = None
    exports_count: int = 0
    depends_on: list[str] = Field(default_factory=list)
    internal: bool = False


class ModuleTreeNode(BaseModel):
    """A node in the module hierarchy tree."""

    name: str
    path: str
    exports: list[str] = Field(default_factory=list)
    depends_on: list[str] = Field(default_factory=list)
    internal: bool = False
    is_package: bool = True  # True if this is a real module in the spec
    children: list["ModuleTreeNode"] = Field(default_factory=list)


class PrincipleSummary(BaseModel):
    """Summary of a design principle."""

    id: str
    statement: str
    has_rationale: bool = False
    implications_count: int = 0
    anti_patterns_count: int = 0


class CountsResult(BaseModel):
    """Counts of various entities."""

    types: int = 0
    functions: int = 0
    features: int = 0
    modules: int = 0
    principles: int = 0


class CoverageResult(BaseModel):
    """Coverage statistics."""

    features_total: int = 0
    features_planned: int = 0
    features_implemented: int = 0
    features_tested: int = 0
    types_with_docs: int = 0
    types_total: int = 0
    methods_with_docs: int = 0
    methods_total: int = 0


class LibraryInfo(BaseModel):
    """Basic library information."""

    name: str
    version: str
    tagline: str | None = None
    python_requires: str | None = None
    repository: str | None = None
    documentation: str | None = None


class InfoResult(BaseModel):
    """Result of the info command."""

    library: LibraryInfo
    extensions: list[str] = Field(default_factory=list)
    counts: CountsResult
    coverage: CoverageResult
