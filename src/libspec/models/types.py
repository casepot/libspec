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

# Cross-reference format with strict validation
CrossReference = Annotated[
    str,
    StringConstraints(
        pattern=r"^([a-z_][a-z0-9_.]*)?#/(types|functions|features|principles|modules)/[a-zA-Z_][a-zA-Z0-9_]*$",
        min_length=1,
    ),
]
"""Reference to another entity: #/types/X, #/functions/Y, or external lib#/types/Z."""

# Type annotation strings (Python type expressions)
TypeAnnotationStr = Annotated[str, StringConstraints(min_length=1)]
"""Python type annotation: int, List[str], Dict[str, Any], Optional[T], etc."""

# Version constraint strings
VersionConstraintStr = Annotated[str, StringConstraints(min_length=1)]
"""Version constraint: >=3.10, 1.2.0, ~=2.0, etc."""

# Environment variable names
EnvVarName = Annotated[str, StringConstraints(pattern=r"^[A-Z_][A-Z0-9_]*$", min_length=1)]
"""Environment variable name in SCREAMING_SNAKE_CASE (e.g., MY_VAR, PYTHONPATH)."""

# Local file/directory path
LocalPath = Annotated[str, StringConstraints(min_length=1)]
"""Local filesystem path, validated in strict mode."""

# -----------------------------------------------------------------------------
# Pattern-Based Constrained Types
# -----------------------------------------------------------------------------

# Function/method reference (dotted Python path)
FunctionReference = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_.]*$", min_length=1),
]
"""Python function/method reference path (e.g., 'module.submodule.function_name')."""

# Simple method/attribute name (no dots, allows dunders)
MethodName = Annotated[
    str,
    StringConstraints(pattern=r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$", min_length=1),
]
"""Simple Python method/attribute name (e.g., 'read_csv', 'on_enter', '__init__').
Snake_case identifiers including dunder methods, no dots."""

# HTTP route path
RoutePath = Annotated[
    str,
    StringConstraints(pattern=r"^/.*$", min_length=1),
]
"""HTTP route path starting with / (e.g., '/users/{id}', '/api/v1/items')."""

# MIME type
MimeType = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z]+/[a-z0-9.+-]+$", min_length=3),
]
"""MIME content type (e.g., 'application/json', 'text/html', 'image/png')."""

# Time window/duration
TimeWindow = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9]+(ms|s|m|h|d)$", min_length=2),
]
"""Time duration string (e.g., '100ms', '30s', '5m', '24h', '7d')."""

# Big-O complexity notation
ComplexityNotation = Annotated[
    str,
    StringConstraints(pattern=r"^O\(.+\)$", min_length=4),
]
"""Big-O complexity notation (e.g., 'O(1)', 'O(n)', 'O(n log n)', 'O(n^2)')."""

# CLI long flag
CliFlag = Annotated[
    str,
    StringConstraints(pattern=r"^--[a-z][a-z0-9-]*$", min_length=3),
]
"""CLI long flag (e.g., '--verbose', '--output-file', '--dry-run')."""

# CLI short flag
ShortFlag = Annotated[
    str,
    StringConstraints(pattern=r"^-[a-zA-Z]$", min_length=2, max_length=2),
]
"""CLI short flag (e.g., '-v', '-o', '-n')."""

# Prometheus-style metric name
MetricName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_]*$", min_length=1),
]
"""Prometheus-compatible metric name (e.g., 'http_requests_total', 'process_cpu_seconds')."""

# Regular expression pattern (validated at parse time via validator if needed)
RegexPattern = Annotated[str, StringConstraints(min_length=1)]
"""Regular expression pattern string."""

# Logger name (dotted Python path for logging)
LoggerName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$", min_length=1),
]
"""Python logger name (dotted path format, e.g., 'mylib' or 'mylib.submodule')."""

# Message queue topic/channel name
TopicName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*([._-][a-z0-9]+)*$", min_length=1),
]
"""Message queue topic/channel name (e.g., 'user-events', 'orders.created')."""

# State tree path
StatePath = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$", min_length=1),
]
"""Dot-separated path in state tree (e.g., 'user.profile.name')."""

# Python entry point group name
EntryPointGroup = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*([._][a-z0-9]+)*$", min_length=1),
]
"""Python entry point group name (e.g., 'console_scripts', 'pytest11')."""

# Path or URL (for mixed fields that accept either)
PathOrUrl = Annotated[str, StringConstraints(min_length=1)]
"""Either a local file path or URL (validated contextually in strict mode)."""

# Environment variable prefix (e.g., 'MYLIB_', 'APP_')
EnvVarPrefix = Annotated[
    str, StringConstraints(pattern=r"^[A-Z_][A-Z0-9_]*_?$", min_length=1)
]
"""Environment variable prefix in SCREAMING_SNAKE_CASE (e.g., 'MYLIB_', 'APP')."""

# Python namespace path (package/module paths)
PythonNamespaceStr = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_]*(\.[a-z_][a-z0-9_]*)*$", min_length=1),
]
"""Python namespace path (e.g., 'mypackage.plugins', 'flask.blueprints')."""

# Text encoding name
TextEncodingStr = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9-]+$", min_length=1)
]
"""Text encoding name (e.g., 'utf-8', 'ascii', 'latin-1')."""

# Datetime format string (strftime/strptime patterns)
DatetimeFormatStr = Annotated[str, StringConstraints(min_length=1)]
"""Python datetime format string for strftime/strptime patterns."""

# Compression algorithm name
CompressionStr = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9-]+$", min_length=1)
]
"""Compression algorithm name (e.g., 'gzip', 'zstd', 'snappy', 'lz4')."""


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
    UNION = "union"  # PEP 604 - union types (X | Y syntax, Python 3.10+)


class FunctionKind(str, Enum):
    """Kind of function definition."""

    FUNCTION = "function"
    DECORATOR = "decorator"
    CONTEXT_MANAGER = "context_manager"
    ASYNC_CONTEXT_MANAGER = "async_context_manager"
    GENERATOR = "generator"
    ASYNC_GENERATOR = "async_generator"
    PROPERTY = "property"  # @property decorated method
    STATICMETHOD = "staticmethod"  # @staticmethod decorated method
    CLASSMETHOD = "classmethod"  # @classmethod decorated method
    COROUTINE = "coroutine"  # Async coroutine (distinct from async generator)


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
