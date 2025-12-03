"""Core models for libspec specifications.

This module defines all the core entity types:
- Parameter, ReturnSpec, YieldSpec, RaisesClause (function components)
- Property, EnumValue, GenericParam (type components)
- Method, Constructor (type members)
- TypeDef, FunctionDef, Feature, Module, Principle (entities)
- Library, LibspecSpec (root containers)
"""

from __future__ import annotations

import re
import warnings
from typing import Any, Literal

from pydantic import ConfigDict, Field, HttpUrl, ValidationInfo, field_validator, model_validator
from typing_extensions import Self

from .base import ExtensibleModel, LibspecModel
from .types import (
    CrossReference,
    ExportOrigin,
    ExtensionName,
    FeatureStatus,
    FunctionKind,
    GenericParamKind,
    GenericVariance,
    KebabCaseId,
    LibraryName,
    ModulePath,
    NonEmptyStr,
    ParameterKind,
    PascalCaseName,
    PythonVersion,
    SchemaVersion,
    ScreamingSnakeCase,
    SemVer,
    TypeAnnotationStr,
    TypeKind,
    VersionConstraintStr,
    Visibility,
)
from .utils import ensure_strict_bool

# -----------------------------------------------------------------------------
# Function/Method Components (Leaf Types)
# -----------------------------------------------------------------------------


class Parameter(LibspecModel):
    """A function or method parameter."""

    name: NonEmptyStr = Field(description="Parameter name")
    type: TypeAnnotationStr | None = Field(
        default=None, description="Parameter type annotation"
    )
    default: str | None = Field(
        default=None, description="Default value (string 'REQUIRED' means no default)"
    )
    description: str | None = Field(
        default=None, description="What this parameter controls"
    )
    kind: ParameterKind = Field(
        default=ParameterKind.POSITIONAL_OR_KEYWORD, description="Parameter kind"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this parameter's type was introduced",
    )


class ReturnSpec(LibspecModel):
    """Return value specification."""

    type: TypeAnnotationStr = Field(description="Return type annotation")
    description: str | None = Field(
        default=None, description="What the return value represents"
    )
    narrows_type: TypeAnnotationStr | None = Field(
        default=None,
        description="Type that input is narrowed to when True (for TypeGuard/TypeIs)",
    )
    narrowing_kind: Literal["type_guard", "type_is"] | None = Field(
        default=None,
        description="Kind of type narrowing: 'type_guard' (PEP 647) or 'type_is' (PEP 742)",
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this return type construct was introduced",
    )

    @model_validator(mode="after")
    def validate_narrowing_fields(self) -> Self:
        """Validate type narrowing field consistency."""
        if (self.narrows_type is None) != (self.narrowing_kind is None):
            raise ValueError(
                "narrows_type and narrowing_kind must be specified together"
            )
        return self


class YieldSpec(LibspecModel):
    """Generator yield specification."""

    type: TypeAnnotationStr = Field(description="Yielded type annotation")
    description: str | None = Field(
        default=None, description="What each yielded value represents"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this yield type construct was introduced",
    )


class RaisesClause(LibspecModel):
    """An exception that may be raised."""

    type: TypeAnnotationStr = Field(description="Exception type name")
    when: str | None = Field(
        default=None, description="Condition under which this exception is raised"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this exception type was introduced",
    )


class DeprecationInfo(LibspecModel):
    """Deprecation information for a function, method, or parameter (PEP 702)."""

    message: str | None = Field(
        default=None,
        description="Deprecation message (shown by type checkers and at runtime)",
    )
    since: VersionConstraintStr | None = Field(
        default=None, description="Version when this was deprecated"
    )
    removal: VersionConstraintStr | None = Field(
        default=None, description="Version when this will be/was removed"
    )
    replacement: CrossReference | None = Field(
        default=None, description="Suggested replacement (cross-reference)"
    )

    @model_validator(mode="after")
    def validate_deprecation_timeline(self) -> "DeprecationInfo":
        """Warn if removal is specified without since."""
        if self.removal is not None and self.since is None:
            warnings.warn(
                "Deprecation specifies 'removal' version without 'since' version; "
                "consider adding when deprecation was introduced",
                UserWarning,
                stacklevel=2,
            )
        return self


# -----------------------------------------------------------------------------
# Type Components (Leaf Types)
# -----------------------------------------------------------------------------


class GenericParam(LibspecModel):
    """A generic type parameter (TypeVar, ParamSpec, or TypeVarTuple)."""

    name: NonEmptyStr = Field(description="Parameter name (e.g., 'T', 'P', 'Ts')")
    kind: GenericParamKind = Field(
        default=GenericParamKind.TYPE_VAR,
        description="Kind of generic parameter: type_var (default), param_spec, or type_var_tuple",
    )
    bound: TypeAnnotationStr | None = Field(
        default=None, description="Upper bound type constraint (TypeVar only)"
    )
    variance: GenericVariance = Field(
        default=GenericVariance.INVARIANT,
        description="Variance of the parameter (TypeVar only)",
    )
    default: TypeAnnotationStr | None = Field(
        default=None,
        description="Default type if not specified (Python 3.13+, PEP 696)",
    )
    constraints: list[TypeAnnotationStr] = Field(
        default_factory=list,
        description="Type constraints for TypeVar (e.g., ['int', 'str'] means T can only be int or str)",
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this generic construct was introduced (e.g., '3.10' for ParamSpec)",
    )

    @model_validator(mode="after")
    def validate_kind_specific_fields(self) -> Self:
        """Validate that fields are appropriate for the parameter kind."""
        if self.kind == GenericParamKind.PARAM_SPEC:
            if self.bound is not None:
                raise ValueError("ParamSpec does not support 'bound' constraint")
            if self.variance != GenericVariance.INVARIANT:
                raise ValueError(
                    "ParamSpec does not support variance; it is always invariant"
                )
            if self.constraints:
                raise ValueError("ParamSpec does not support type constraints")
        elif self.kind == GenericParamKind.TYPE_VAR_TUPLE:
            if self.bound is not None:
                raise ValueError("TypeVarTuple does not support 'bound' constraint")
            if self.variance != GenericVariance.INVARIANT:
                raise ValueError("TypeVarTuple does not support explicit variance")
            if self.constraints:
                raise ValueError("TypeVarTuple does not support type constraints")
        elif self.kind == GenericParamKind.TYPE_VAR:
            # TypeVar: bound and constraints are mutually exclusive
            if self.bound is not None and self.constraints:
                raise ValueError(
                    f"TypeVar '{self.name}' cannot have both 'bound' and 'constraints'; "
                    "use bound for upper bound OR constraints for allowed types"
                )
        return self


class Property(ExtensibleModel):
    """An instance property or attribute."""

    name: NonEmptyStr = Field(description="Property name")
    type: TypeAnnotationStr | None = Field(
        default=None, description="Property type annotation"
    )
    readonly: bool = Field(
        default=False, description="Whether this is a read-only property"
    )
    readonly_marker: bool | None = Field(
        default=None,
        description="For TypedDict: whether this uses PEP 705 ReadOnly[T] marker (Python 3.13+)",
    )
    default: str | None = Field(
        default=None, description="Default value (as a string representation)"
    )
    description: str | None = Field(
        default=None, description="What this property represents"
    )
    visibility: Visibility | None = Field(
        default=None,
        description="Symbol visibility (public/private/mangled). Defaults to public.",
    )
    required: bool | None = Field(
        default=None,
        description="For TypedDict properties: whether this key is required. None inherits from total.",
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version required for this property's type annotation",
    )

    @model_validator(mode="after")
    def validate_readonly_marker(self) -> Self:
        """Validate that readonly_marker=True requires readonly=True."""
        if self.readonly_marker is True and not self.readonly:
            raise ValueError(
                f"Property '{self.name}': readonly_marker=True requires readonly=True"
            )
        return self


class EnumValue(LibspecModel):
    """An enum member value."""

    name: NonEmptyStr = Field(description="Enum member name")
    value: str | int | None = Field(
        default=None, description="Enum member value (e.g., 'auto()' or explicit value)"
    )
    description: str | None = Field(
        default=None, description="What this enum value represents"
    )


# -----------------------------------------------------------------------------
# Type Members (Container Types)
# -----------------------------------------------------------------------------


class OverloadSpec(LibspecModel):
    """An overloaded signature variant for type-checking (@overload decorator)."""

    signature: NonEmptyStr = Field(description="The overloaded signature variant")
    parameters: list[Parameter] = Field(
        default_factory=list,
        description="Parameter specifications for this overload",
    )
    returns: ReturnSpec | None = Field(
        default=None, description="Return type for this overload"
    )
    description: str | None = Field(
        default=None, description="When this overload variant applies"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this overload variant was introduced",
    )


class Method(ExtensibleModel):
    """A method definition."""

    name: NonEmptyStr = Field(description="Method name")
    signature: NonEmptyStr = Field(
        description="Full signature including parameters and return type"
    )
    description: str | None = Field(
        default=None, description="What this method does"
    )
    parameters: list[Parameter] = Field(
        default_factory=list, description="Detailed parameter specifications"
    )
    returns: ReturnSpec | None = Field(
        default=None, description="Return value specification"
    )
    yields: YieldSpec | None = Field(
        default=None, description="Yield value specification for sync generators"
    )
    async_yields: YieldSpec | None = Field(
        default=None, description="Yield value specification for async generators"
    )
    overloads: list["OverloadSpec"] = Field(
        default_factory=list,
        description="@overload signature variants for type-checking",
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="State requirements before calling this method",
    )
    postconditions: list[str] = Field(
        default_factory=list,
        description="Guaranteed state after this method completes",
    )
    raises: list[RaisesClause] = Field(
        default_factory=list, description="Exceptions this method may raise"
    )
    inherited_from: CrossReference | None = Field(
        default=None,
        description="Base class this method is inherited from (if any)",
    )
    visibility: Visibility | None = Field(
        default=None,
        description="Symbol visibility (public/private/mangled/dunder). Defaults to public.",
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this method or its features were introduced",
    )
    is_override: bool | None = Field(
        default=None,
        description="Whether this method uses @override decorator (PEP 698, Python 3.12+)",
    )
    deprecation: "DeprecationInfo | None" = Field(
        default=None,
        description="Deprecation information if this method is deprecated (PEP 702)",
    )

    @field_validator("signature")
    @classmethod
    def validate_signature_format(cls, v: str) -> str:
        """Validate signature starts with '(' for parameter list."""
        if v and not v.strip().startswith("("):
            warnings.warn(
                f"Signature should start with '(' for parameter list: {v!r}",
                UserWarning,
                stacklevel=2,
            )
        return v

    @model_validator(mode="after")
    def validate_yield_consistency(self) -> Self:
        """Validate that yields and async_yields are consistent."""
        if self.yields is not None and self.async_yields is not None:
            raise ValueError(
                "Cannot specify both 'yields' and 'async_yields'; use one based on generator type"
            )
        # Warn if generator specifies explicit return
        if (self.yields is not None or self.async_yields is not None) and self.returns is not None:
            warnings.warn(
                f"Generator method '{self.name}' specifies 'returns'; "
                "generators typically don't need explicit return type",
                UserWarning,
                stacklevel=2,
            )
        return self


class Constructor(LibspecModel):
    """Constructor specification."""

    signature: NonEmptyStr = Field(description="Constructor signature")
    parameters: list[Parameter] = Field(
        default_factory=list, description="Constructor parameters"
    )
    validates: list[str] = Field(
        default_factory=list, description="Validation performed during construction"
    )
    raises: list[RaisesClause] = Field(
        default_factory=list,
        description="Exceptions that may be raised during construction",
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this constructor pattern was introduced",
    )


# -----------------------------------------------------------------------------
# Entity Types
# -----------------------------------------------------------------------------


class TypeDef(ExtensibleModel):
    """A type definition (class, protocol, enum, etc.)."""

    name: PascalCaseName = Field(description="Type name")
    kind: TypeKind = Field(description="Kind of type")
    module: ModulePath = Field(description="Module where this type is defined")
    generic_params: list[GenericParam] = Field(
        default_factory=list, description="Generic type parameters"
    )
    bases: list[CrossReference] = Field(
        default_factory=list, description="Base classes or protocols"
    )
    docstring: str | None = Field(
        default=None, description="What this type represents"
    )
    type_target: TypeAnnotationStr | None = Field(
        default=None, description="For type_alias: the aliased type"
    )
    properties: list[Property] = Field(
        default_factory=list, description="Instance properties/attributes"
    )
    methods: list[Method] = Field(
        default_factory=list, description="Instance methods"
    )
    class_methods: list[Method] = Field(
        default_factory=list, description="Class methods"
    )
    static_methods: list[Method] = Field(
        default_factory=list, description="Static methods"
    )
    values: list[EnumValue] = Field(
        default_factory=list, description="Enum values (only for kind='enum')"
    )
    invariants: list[str] = Field(
        default_factory=list,
        description="Statements that are always true for valid instances",
    )
    construction: Constructor | None = Field(
        default=None, description="Constructor specification"
    )
    related: list[CrossReference] = Field(
        default_factory=list,
        description="Related types or functions (cross-references)",
    )
    example: str | None = Field(
        default=None, description="Code example showing typical usage"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this type or its features were introduced",
    )
    # TypedDict-specific fields (PEP 589)
    typed_dict_total: bool | None = Field(
        default=None,
        description="For TypedDict: whether all keys are required by default (total=True/False)",
    )
    typed_dict_closed: bool | None = Field(
        default=None,
        description="For TypedDict: whether extra keys are forbidden (PEP 728, Python 3.13+)",
    )

    @model_validator(mode="after")
    def check_type_completeness(self) -> Self:
        """Validate type completeness based on kind."""
        # C005: enum-no-values - Enums should have values
        if self.kind == TypeKind.ENUM and not self.values:
            raise ValueError(f"Enum '{self.name}' must have values defined")

        # C006: protocol-no-methods - Protocols should define interface
        if self.kind == TypeKind.PROTOCOL:
            if not self.methods and not self.properties:
                raise ValueError(
                    f"Protocol '{self.name}' must have methods or properties"
                )

        # Validate TypedDict-specific fields only apply to TypedDicts
        if self.kind != TypeKind.TYPED_DICT:
            if self.typed_dict_total is not None:
                raise ValueError(
                    f"'{self.name}': typed_dict_total is only valid for TypedDict types"
                )
            if self.typed_dict_closed is not None:
                raise ValueError(
                    f"'{self.name}': typed_dict_closed is only valid for TypedDict types"
                )

        # NewType must have type_target (the wrapped type)
        if self.kind == TypeKind.NEWTYPE:
            if not self.type_target:
                raise ValueError(
                    f"NewType '{self.name}' must specify type_target (the wrapped type)"
                )

        # Type aliases should have type_target (the aliased type)
        if self.kind == TypeKind.TYPE_ALIAS:
            if not self.type_target:
                warnings.warn(
                    f"TypeAlias '{self.name}' should specify type_target (the aliased type)",
                    UserWarning,
                    stacklevel=2,
                )

        # Literal types cannot have methods or properties (they're value types)
        if self.kind == TypeKind.LITERAL:
            if self.methods or self.properties:
                raise ValueError(
                    f"Literal type '{self.name}' cannot have methods or properties"
                )

        # GenericAlias must have type_target (the aliased generic type)
        if self.kind == TypeKind.GENERIC_ALIAS:
            if not self.type_target:
                raise ValueError(
                    f"GenericAlias '{self.name}' must specify type_target (the aliased type)"
                )

        return self


class FunctionDef(ExtensibleModel):
    """A top-level function definition."""

    name: str = Field(description="Function name")
    kind: FunctionKind = Field(
        default=FunctionKind.FUNCTION, description="Kind of callable"
    )
    module: ModulePath = Field(description="Module where this function is defined")
    signature: NonEmptyStr = Field(
        description="Full signature including parameters and return type"
    )
    generic_params: list[GenericParam] = Field(
        default_factory=list, description="Generic type parameters"
    )
    parameters: list[Parameter] = Field(
        default_factory=list, description="Detailed parameter specifications"
    )
    returns: ReturnSpec | None = Field(
        default=None, description="Return value specification"
    )
    yields: YieldSpec | None = Field(
        default=None, description="Yield value specification for sync generators"
    )
    async_yields: YieldSpec | None = Field(
        default=None, description="Yield value specification for async generators"
    )
    overloads: list[OverloadSpec] = Field(
        default_factory=list,
        description="@overload signature variants for type-checking",
    )
    description: str | None = Field(
        default=None, description="What this function does"
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="State requirements before calling this function",
    )
    postconditions: list[str] = Field(
        default_factory=list,
        description="Guaranteed state after this function completes",
    )
    invariants: list[str] = Field(
        default_factory=list,
        description="Conditions preserved by this function",
    )
    raises: list[RaisesClause] = Field(
        default_factory=list, description="Exceptions this function may raise"
    )
    idempotent: bool | None = Field(
        default=None, description="Whether calling multiple times has same effect as once"
    )
    pure: bool | None = Field(
        default=None, description="Whether function has no side effects"
    )
    deterministic: bool | None = Field(
        default=None, description="Whether same inputs always produce same outputs"
    )
    related: list[CrossReference] = Field(
        default_factory=list,
        description="Related types or functions (cross-references)",
    )
    example: str | None = Field(
        default=None, description="Code example showing typical usage"
    )
    python_added: PythonVersion | None = Field(
        default=None,
        description="Python version when this function or its features were introduced",
    )
    deprecation: DeprecationInfo | None = Field(
        default=None,
        description="Deprecation information if this function is deprecated (PEP 702)",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """N004: Function names must be snake_case (dunder methods allowed)."""
        # Allow dunder methods like __init__, __str__, etc.
        if v.startswith("__") and v.endswith("__"):
            return v
        # Match lint rule pattern exactly: no trailing/leading/double underscores
        if not re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", v):
            raise ValueError(f"Function name '{v}' must be snake_case")
        return v

    @field_validator("signature")
    @classmethod
    def validate_signature_format(cls, v: str) -> str:
        """Validate signature starts with '(' for parameter list."""
        if v and not v.strip().startswith("("):
            warnings.warn(
                f"Signature should start with '(' for parameter list: {v!r}",
                UserWarning,
                stacklevel=2,
            )
        return v

    @field_validator("idempotent", "pure", "deterministic", mode="before")
    @classmethod
    def enforce_strict_flags(cls, value: Any, info: ValidationInfo) -> Any:
        return ensure_strict_bool(value, info, info.field_name or "flag")

    @model_validator(mode="after")
    def validate_yield_consistency(self) -> Self:
        """Validate that yields and async_yields are consistent with function kind."""
        if self.yields is not None and self.async_yields is not None:
            raise ValueError(
                "Cannot specify both 'yields' and 'async_yields'; use one based on generator type"
            )
        if self.kind == FunctionKind.GENERATOR and self.async_yields is not None:
            raise ValueError(
                "Generator functions should use 'yields', not 'async_yields'"
            )
        if self.kind == FunctionKind.ASYNC_GENERATOR and self.yields is not None:
            raise ValueError(
                "Async generator functions should use 'async_yields', not 'yields'"
            )
        # Warn if generator specifies explicit return (generators return generator objects)
        if (self.yields is not None or self.async_yields is not None) and self.returns is not None:
            warnings.warn(
                f"Generator function '{self.name}' specifies 'returns'; "
                "generators typically don't need explicit return type (they return generator objects)",
                UserWarning,
                stacklevel=2,
            )
        return self


class Feature(ExtensibleModel):
    """A behavioral specification with test steps."""

    id: KebabCaseId = Field(description="Unique identifier for this feature")
    category: ScreamingSnakeCase = Field(
        description="Feature category (SCREAMING_SNAKE_CASE)"
    )
    summary: str | None = Field(
        default=None, description="Brief one-line summary"
    )
    description: str | None = Field(
        default=None, description="Detailed description (Markdown supported)"
    )
    steps: list[NonEmptyStr] = Field(
        default_factory=list,
        description="Verification/test steps (at least one recommended; enforced by lint rule C001)",
    )
    references: list[CrossReference] = Field(
        default_factory=list, description="Related types, functions, or features"
    )
    status: FeatureStatus = Field(
        default=FeatureStatus.PLANNED, description="Implementation status"
    )
    breaking_since: VersionConstraintStr | None = Field(
        default=None, description="Version where this became a breaking change"
    )
    v1_planned: bool | None = Field(
        default=None, description="Whether planned for v1.0 release"
    )


class Export(LibspecModel):
    """A symbol exported from a module with origin tracking."""

    name: NonEmptyStr = Field(description="Exported symbol name")
    origin: ExportOrigin = Field(
        default=ExportOrigin.DEFINED,
        description="How this symbol is exported: defined, reexported, or aliased",
    )
    source_module: ModulePath | None = Field(
        default=None,
        description="For reexported/aliased: the module the symbol was imported from",
    )
    source_name: NonEmptyStr | None = Field(
        default=None,
        description="For aliased: the original name of the symbol (if different)",
    )
    public: bool = Field(
        default=True,
        description="Whether this symbol is in __all__ (public API)",
    )

    @model_validator(mode="after")
    def validate_export_fields(self) -> Self:
        """Validate that origin-specific fields are consistent."""
        if self.origin == ExportOrigin.DEFINED:
            if self.source_module is not None or self.source_name is not None:
                raise ValueError(
                    "Exports with origin='defined' should not have source_module or source_name"
                )
        elif self.origin == ExportOrigin.REEXPORTED:
            if self.source_module is None:
                raise ValueError(
                    "Exports with origin='reexported' must specify source_module"
                )
            if self.source_name is not None:
                raise ValueError(
                    "Exports with origin='reexported' should not have source_name (use 'aliased' for renamed exports)"
                )
        elif self.origin == ExportOrigin.ALIASED:
            if self.source_module is None:
                raise ValueError(
                    "Exports with origin='aliased' must specify source_module"
                )
            if self.source_name is None:
                raise ValueError(
                    "Exports with origin='aliased' must specify source_name (the original name)"
                )
        return self


class Module(LibspecModel):
    """A Python module or package."""

    path: ModulePath = Field(description="Dotted module path (e.g., 'mylib.submodule')")
    description: str | None = Field(
        default=None, description="What this module provides"
    )
    exports: list[str | Export] = Field(
        default_factory=list,
        description="Public names exported by this module (strings for simple names, Export for detailed tracking)",
    )
    depends_on: list[str] = Field(
        default_factory=list, description="Internal module dependencies"
    )
    external_deps: list[str] = Field(
        default_factory=list, description="External package dependencies"
    )
    internal: bool = Field(
        default=False, description="Whether this is a private/internal module"
    )


class Principle(LibspecModel):
    """A design principle that guides library decisions."""

    id: KebabCaseId = Field(description="Unique identifier for this principle")
    statement: NonEmptyStr = Field(description="Brief principle statement")
    rationale: str | None = Field(
        default=None, description="Why this principle exists"
    )
    implications: list[str] = Field(
        default_factory=list, description="Concrete implications of this principle"
    )
    anti_patterns: list[str] = Field(
        default_factory=list, description="What this principle forbids"
    )


# -----------------------------------------------------------------------------
# Root Containers
# -----------------------------------------------------------------------------


class Library(ExtensibleModel):
    """Root container for a library specification."""

    name: LibraryName = Field(
        description="Package name (lowercase, underscores allowed)"
    )
    version: SemVer = Field(description="Semantic version string")
    python_requires: VersionConstraintStr | None = Field(
        default=None, description="Python version requirement (e.g., '>=3.10')"
    )
    tagline: str | None = Field(
        default=None, description="One-line description of the library"
    )
    description: str | None = Field(
        default=None, description="Longer description (Markdown supported)"
    )
    repository: HttpUrl | None = Field(
        default=None, description="URL to source repository"
    )
    documentation: HttpUrl | None = Field(
        default=None, description="URL to documentation"
    )
    principles: list[Principle] = Field(
        default_factory=list, description="Design principles guiding the library"
    )
    modules: list[Module] = Field(
        default_factory=list, description="Package structure and module definitions"
    )
    types: list[TypeDef] = Field(
        default_factory=list,
        description="Type definitions (classes, protocols, enums, etc.)",
    )
    functions: list[FunctionDef] = Field(
        default_factory=list, description="Top-level function definitions"
    )
    features: list[Feature] = Field(
        default_factory=list, description="Behavioral specifications with test steps"
    )


class LibspecSpec(LibspecModel):
    """Root model for a libspec specification file."""

    schema_: SchemaVersion | None = Field(
        default=None, alias="$schema", description="Schema version identifier"
    )
    extensions: list[ExtensionName] = Field(
        default_factory=list,
        description="List of extensions to apply to this specification",
    )
    library: Library = Field(description="The library specification")

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        json_schema_extra={
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://libspec.dev/schema/core.schema.json",
            "title": "LibSpec Core Schema",
            "description": "Schema for library specification documents",
        },
    )
