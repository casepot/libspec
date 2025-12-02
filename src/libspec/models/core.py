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

from pydantic import AnyUrl, Field, conlist, field_validator, model_validator
from typing_extensions import Self

from .base import ExtensibleModel, LibspecModel
from .types import (
    ExtensionName,
    FeatureStatus,
    FunctionKind,
    GenericVariance,
    KebabCaseId,
    LibraryName,
    ParameterKind,
    SchemaVersion,
    ScreamingSnakeCase,
    SemVer,
    TypeKind,
)

# -----------------------------------------------------------------------------
# Function/Method Components (Leaf Types)
# -----------------------------------------------------------------------------


class Parameter(LibspecModel):
    """A function or method parameter."""

    name: str = Field(description="Parameter name")
    type: str | None = Field(default=None, description="Parameter type annotation")
    default: str | None = Field(
        default=None, description="Default value (string 'REQUIRED' means no default)"
    )
    description: str | None = Field(
        default=None, description="What this parameter controls"
    )
    kind: ParameterKind = Field(
        default=ParameterKind.POSITIONAL_OR_KEYWORD, description="Parameter kind"
    )


class ReturnSpec(LibspecModel):
    """Return value specification."""

    type: str = Field(description="Return type annotation")
    description: str | None = Field(
        default=None, description="What the return value represents"
    )


class YieldSpec(LibspecModel):
    """Generator yield specification."""

    type: str = Field(description="Yielded type annotation")
    description: str | None = Field(
        default=None, description="What each yielded value represents"
    )


class RaisesClause(LibspecModel):
    """An exception that may be raised."""

    type: str = Field(description="Exception type name")
    when: str | None = Field(
        default=None, description="Condition under which this exception is raised"
    )


# -----------------------------------------------------------------------------
# Type Components (Leaf Types)
# -----------------------------------------------------------------------------


class GenericParam(LibspecModel):
    """A generic type parameter."""

    name: str = Field(description="Parameter name (e.g., 'T', 'K', 'V')")
    bound: str | None = Field(default=None, description="Upper bound type constraint")
    variance: GenericVariance = Field(
        default=GenericVariance.INVARIANT, description="Variance of the parameter"
    )
    default: str | None = Field(
        default=None, description="Default type if not specified (Python 3.12+)"
    )


class Property(ExtensibleModel):
    """An instance property or attribute."""

    name: str = Field(description="Property name")
    type: str | None = Field(default=None, description="Property type annotation")
    readonly: bool = Field(
        default=False, description="Whether this is a read-only property"
    )
    default: str | None = Field(
        default=None, description="Default value (as a string representation)"
    )
    description: str | None = Field(
        default=None, description="What this property represents"
    )


class EnumValue(LibspecModel):
    """An enum member value."""

    name: str = Field(description="Enum member name")
    value: str | int | None = Field(
        default=None, description="Enum member value (e.g., 'auto()' or explicit value)"
    )
    description: str | None = Field(
        default=None, description="What this enum value represents"
    )


# -----------------------------------------------------------------------------
# Type Members (Container Types)
# -----------------------------------------------------------------------------


class Method(ExtensibleModel):
    """A method definition."""

    name: str = Field(description="Method name")
    signature: str = Field(
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
    inherited_from: str | None = Field(
        default=None,
        description="Base class this method is inherited from (if any)",
    )


class Constructor(LibspecModel):
    """Constructor specification."""

    signature: str = Field(description="Constructor signature")
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


# -----------------------------------------------------------------------------
# Entity Types
# -----------------------------------------------------------------------------


class TypeDef(ExtensibleModel):
    """A type definition (class, protocol, enum, etc.)."""

    name: str = Field(description="Type name")
    kind: TypeKind = Field(description="Kind of type")
    module: str = Field(description="Module where this type is defined")
    generic_params: list[GenericParam] = Field(
        default_factory=list, description="Generic type parameters"
    )
    bases: list[str] = Field(
        default_factory=list, description="Base classes or protocols"
    )
    docstring: str | None = Field(
        default=None, description="What this type represents"
    )
    type_target: str | None = Field(
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
    related: list[str] = Field(
        default_factory=list,
        description="Related types or functions (cross-references)",
    )
    example: str | None = Field(
        default=None, description="Code example showing typical usage"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """N003: Type names must be PascalCase."""
        if not re.match(r"^[A-Z][a-zA-Z0-9]*$", v):
            raise ValueError(f"Type name '{v}' must be PascalCase")
        return v

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

        return self


class FunctionDef(ExtensibleModel):
    """A top-level function definition."""

    name: str = Field(description="Function name")
    kind: FunctionKind = Field(
        default=FunctionKind.FUNCTION, description="Kind of callable"
    )
    module: str = Field(description="Module where this function is defined")
    signature: str = Field(
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
        default=None, description="Yield value specification for generators"
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
    related: list[str] = Field(
        default_factory=list,
        description="Related types or functions (cross-references)",
    )
    example: str | None = Field(
        default=None, description="Code example showing typical usage"
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
    steps: conlist(str, min_length=1) = Field(
        default_factory=list, description="Verification/test steps (at least one)"
    )
    references: list[str] = Field(
        default_factory=list, description="Related types, functions, or features"
    )
    status: FeatureStatus = Field(
        default=FeatureStatus.PLANNED, description="Implementation status"
    )
    breaking_since: str | None = Field(
        default=None, description="Version where this became a breaking change"
    )
    v1_planned: bool | None = Field(
        default=None, description="Whether planned for v1.0 release"
    )


class Module(LibspecModel):
    """A Python module or package."""

    path: str = Field(description="Dotted module path (e.g., 'mylib.submodule')")
    description: str | None = Field(
        default=None, description="What this module provides"
    )
    exports: list[str] = Field(
        default_factory=list, description="Public names exported by this module"
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
    statement: str = Field(description="Brief principle statement")
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
    python_requires: str | None = Field(
        default=None, description="Python version requirement (e.g., '>=3.10')"
    )
    tagline: str | None = Field(
        default=None, description="One-line description of the library"
    )
    description: str | None = Field(
        default=None, description="Longer description (Markdown supported)"
    )
    repository: AnyUrl | None = Field(
        default=None, description="URL to source repository"
    )
    documentation: AnyUrl | None = Field(
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

    model_config = LibspecModel.model_config.copy()
    model_config["json_schema_extra"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://libspec.dev/schema/core.schema.json",
        "title": "LibSpec Core Schema",
        "description": "Schema for library specification documents",
    }
