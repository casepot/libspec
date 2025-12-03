"""Type definitions, enums, and constrained types for libspec models."""

from enum import Enum
from typing import Annotated

from pydantic import StringConstraints

# -----------------------------------------------------------------------------
# Constrained String Types
# -----------------------------------------------------------------------------

# Identifier patterns matching lint rule definitions exactly
KebabCaseId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", min_length=1),
]
"""Kebab-case identifier (e.g., 'my-feature-id'). Matches N001/N002 lint rules."""

SnakeCaseId = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", min_length=1),
]
"""Snake_case identifier (e.g., 'my_function_name'). Matches N004 lint rule."""

PascalCaseName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][a-zA-Z0-9]*$", min_length=1),
]
"""PascalCase name (e.g., 'MyClassName'). Matches N003 lint rule."""

ScreamingSnakeCase = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][A-Z0-9]*(_[A-Z0-9]+)*$", min_length=1),
]
"""SCREAMING_SNAKE_CASE (e.g., 'FEATURE_CATEGORY'). Matches N006 lint rule."""

# Library metadata patterns
LibraryName = Annotated[
    str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$", min_length=1, max_length=100)
]
"""Library name pattern (lowercase with underscores)."""

SemVer = Annotated[str, StringConstraints(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+.*$")]
"""Semantic version string (e.g., '1.2.3' or '1.2.3-beta.1')."""

SchemaVersion = Annotated[str, StringConstraints(pattern=r"^libspec/[0-9]+\.[0-9]+$")]
"""Schema version string (e.g., 'libspec/1.0')."""

# Module path pattern
ModulePath = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_.]*$", min_length=1),
]
"""Python module path (e.g., 'mypackage.submodule')."""

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
"""Generic non-empty string for required text fields."""


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
    TYPED_DICT = "typed_dict"  # PEP 589
    NEWTYPE = "newtype"  # PEP 484 - distinct wrapper type (e.g., UserId = NewType('UserId', int))
    LITERAL = "literal"  # PEP 586 - literal type definitions
    GENERIC_ALIAS = "generic_alias"  # PEP 695 - type X[T] = ... syntax (Python 3.12+)


class FunctionKind(str, Enum):
    """Kind of function definition."""

    FUNCTION = "function"
    DECORATOR = "decorator"
    CONTEXT_MANAGER = "context_manager"
    ASYNC_CONTEXT_MANAGER = "async_context_manager"
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"


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


class BehaviorMode(str, Enum):
    """Mode for handling implicit/explicit behaviors.

    Common pattern used across extensions for specifying how the library
    handles automatic vs manual operations (e.g., type coercion, validation).
    """

    IMPLICIT = "implicit"  # Automatically applied
    EXPLICIT = "explicit"  # Must be explicitly requested
    ERROR = "error"  # Raise an error
    WARN = "warn"  # Log a warning but continue


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
    ML = "ml"  # PLANNED: Not yet implemented - ML-specific fields pending design
    SERIALIZATION = "serialization"

    # Concern extensions
    ERRORS = "errors"
    PERF = "perf"
    SAFETY = "safety"
    CONFIG = "config"
    VERSIONING = "versioning"
    OBSERVABILITY = "observability"
    LIFECYCLE = "lifecycle"


class GenericParamKind(str, Enum):
    """Kind of generic type parameter.

    Supports the three parameter specification constructs in Python's typing system:
    - TypeVar (PEP 484): Standard type variable, e.g., T = TypeVar('T')
    - ParamSpec (PEP 612, Python 3.10+): Captures function parameter types
    - TypeVarTuple (PEP 646, Python 3.11+): Variadic type variable
    """

    TYPE_VAR = "type_var"
    PARAM_SPEC = "param_spec"
    TYPE_VAR_TUPLE = "type_var_tuple"


class ExportOrigin(str, Enum):
    """Origin of an exported symbol from a module."""

    DEFINED = "defined"  # Symbol is defined in this module
    REEXPORTED = "reexported"  # Symbol is imported and re-exported
    ALIASED = "aliased"  # Symbol is re-exported under a different name


class Visibility(str, Enum):
    """Symbol visibility level following Python conventions."""

    PUBLIC = "public"  # Normal public API
    PRIVATE = "private"  # Single underscore (_name) - internal use
    MANGLED = "mangled"  # Double underscore (__name) - name mangling
    DUNDER = "dunder"  # Dunder methods (__init__, __str__) - special


# Python version constraint for tracking feature introduction
PythonVersion = Annotated[
    str,
    StringConstraints(pattern=r"^3\.\d+(\+)?$", min_length=3),
]
"""Python version string (e.g., '3.10', '3.11+'). For tracking when features were introduced."""
