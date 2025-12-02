"""Type definitions, enums, and constrained types for libspec models."""

from enum import Enum
from typing import Annotated

from pydantic import Field

# -----------------------------------------------------------------------------
# Constrained String Types
# -----------------------------------------------------------------------------

# Identifier patterns matching lint rule definitions exactly
KebabCaseId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", min_length=1)]
"""Kebab-case identifier (e.g., 'my-feature-id'). Matches N001/N002 lint rules."""

SnakeCaseId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", min_length=1)]
"""Snake_case identifier (e.g., 'my_function_name'). Matches N004 lint rule."""

PascalCaseName = Annotated[str, Field(pattern=r"^[A-Z][a-zA-Z0-9]*$", min_length=1)]
"""PascalCase name (e.g., 'MyClassName'). Matches N003 lint rule."""

ScreamingSnakeCase = Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$", min_length=1)]
"""SCREAMING_SNAKE_CASE (e.g., 'FEATURE_CATEGORY'). Matches N006 lint rule."""

# Library metadata patterns
LibraryName = Annotated[
    str, Field(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=100)
]
"""Library name pattern (lowercase with underscores)."""

SemVer = Annotated[str, Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+.*$")]
"""Semantic version string (e.g., '1.2.3' or '1.2.3-beta.1')."""

SchemaVersion = Annotated[str, Field(pattern=r"^libspec/[0-9]+\.[0-9]+$")]
"""Schema version string (e.g., 'libspec/1.0')."""

# Module path pattern
ModulePath = Annotated[str, Field(pattern=r"^[a-z_][a-z0-9_.]*$", min_length=1)]
"""Python module path (e.g., 'mypackage.submodule')."""


# -----------------------------------------------------------------------------
# Core Enums
# -----------------------------------------------------------------------------


class TypeKind(str, Enum):
    """Kind of type definition."""

    CLASS = "class"
    DATACLASS = "dataclass"
    PROTOCOL = "protocol"
    ENUM = "enum"
    TYPE_ALIAS = "type_alias"
    NAMEDTUPLE = "namedtuple"


class FunctionKind(str, Enum):
    """Kind of function definition."""

    FUNCTION = "function"
    DECORATOR = "decorator"
    CONTEXT_MANAGER = "context_manager"
    ASYNC_CONTEXT_MANAGER = "async_context_manager"


class ParameterKind(str, Enum):
    """Kind of function/method parameter."""

    POSITIONAL_ONLY = "positional_only"
    POSITIONAL_OR_KEYWORD = "positional_or_keyword"
    KEYWORD_ONLY = "keyword_only"
    VAR_POSITIONAL = "var_positional"
    VAR_KEYWORD = "var_keyword"


class FeatureStatus(str, Enum):
    """Implementation status of a feature."""

    PLANNED = "planned"
    IMPLEMENTED = "implemented"
    TESTED = "tested"


class GenericVariance(str, Enum):
    """Variance of a generic type parameter."""

    INVARIANT = "invariant"
    COVARIANT = "covariant"
    CONTRAVARIANT = "contravariant"


class ExtensionName(str, Enum):
    """Available extension names."""

    # Domain extensions
    ASYNC = "async"
    WEB = "web"
    DATA = "data"
    CLI = "cli"
    ORM = "orm"
    TESTING = "testing"
    EVENTS = "events"
    STATE = "state"
    PLUGINS = "plugins"
    ML = "ml"

    # Concern extensions
    ERRORS = "errors"
    PERF = "perf"
    SAFETY = "safety"
    CONFIG = "config"
    VERSIONING = "versioning"
    OBSERVABILITY = "observability"
    LIFECYCLE = "lifecycle"
