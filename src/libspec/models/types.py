"""Type definitions, enums, and constrained types for libspec models."""

import re
from decimal import Decimal
from enum import Enum
from pathlib import Path as PathlibPath
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BeforeValidator,
    DirectoryPath,
    Field,
    FilePath,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    PositiveInt,
    StringConstraints,
    ValidationInfo,
)

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

SemVer = Annotated[
    str,
    StringConstraints(
        pattern=r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
        r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
        r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
        r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
    ),
]
"""Semantic version string per semver.org spec (e.g., '1.2.3', '1.2.3-beta.1', '1.0.0+build.123')."""

SchemaVersion = Annotated[str, StringConstraints(pattern=r"^libspec/[0-9]+\.[0-9]+$")]
"""Schema version string (e.g., 'libspec/1.0')."""

# Module path pattern
ModulePath = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$", min_length=1),
]
"""Python module path (e.g., 'mypackage.submodule')."""

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
"""Generic non-empty string for required text fields."""

# Cross-reference format with strict validation
# Entity names can be:
#   - PascalCase for types (TypeName)
#   - snake_case for functions (function_name)
#   - kebab-case for features/principles (feature-id)
#   - dotted for modules (mylib.submodule)
CrossReference = Annotated[
    str,
    StringConstraints(
        pattern=r"^([a-z_][a-z0-9_.]*)?#/(types|functions|features|principles|modules)/[a-zA-Z_][a-zA-Z0-9_-]*$",
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
LocalPath = PathlibPath
"""Local filesystem path. Pydantic auto-serializes to string in JSON."""

# -----------------------------------------------------------------------------
# Pattern-Based Constrained Types
# -----------------------------------------------------------------------------

# Function/method reference (dotted Python path)
FunctionReference = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)*$", min_length=1),
]
"""Python function/method reference path (e.g., 'module.submodule.function_name')."""

# Simple method/attribute name (no dots, allows dunders)
MethodName = Annotated[
    str,
    StringConstraints(pattern=r"^(?:__[a-z][a-z0-9_]*__|_?[a-z][a-z0-9]*(?:_[a-z0-9]+)*)$", min_length=1),
]
"""Simple Python method/attribute name (e.g., 'read_csv', 'on_enter', '__init__').
Snake_case identifiers including dunder methods, no dots."""


def _validate_snake_case_or_dunder(value: str) -> str:
    """Validate snake_case or dunder method name."""
    if value.startswith("__") and value.endswith("__"):
        return value  # Valid dunder
    if not re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", value):
        raise ValueError(f"Name '{value}' must be snake_case or __dunder__")
    return value


SnakeCaseOrDunderName = Annotated[str, AfterValidator(_validate_snake_case_or_dunder)]
"""Function/method name: snake_case or __dunder__ format."""

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
    StringConstraints(pattern=r"^--[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", min_length=3),
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

# Regular expression pattern (validated at parse time)
def _validate_regex(value: str) -> str:
    """Validate that a string is a valid regular expression."""
    try:
        re.compile(value)
    except re.error as exc:
        raise ValueError(f"Invalid regex pattern: {exc}") from exc
    return value


RegexPattern = Annotated[str, StringConstraints(min_length=1), AfterValidator(_validate_regex)]
"""Regular expression pattern string. Validated to be a syntactically valid regex."""

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
PathOrUrl = PathlibPath | str
"""Local path or URL string. URLs (http://, https://, file://) pass through as strings."""

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
# TODO: Currently unused - consider removal or document intended use
DatetimeFormatStr = Annotated[str, StringConstraints(min_length=1)]
"""Python datetime format string for strftime/strptime patterns."""

# Compression algorithm name
# TODO: Currently unused - consider removal or document intended use
CompressionStr = Annotated[
    str, StringConstraints(pattern=r"^[a-z0-9-]+$", min_length=1)
]
"""Compression algorithm name (e.g., 'gzip', 'zstd', 'snappy', 'lz4')."""


# -----------------------------------------------------------------------------
# Numeric Constrained Types
# -----------------------------------------------------------------------------

# HTTP status codes
HttpStatusCode = Annotated[int, Field(ge=100, le=599)]
"""HTTP status code (100-599)."""

PortNumber = Annotated[int, Field(ge=1, le=65535)]
"""TCP/UDP port number (1-65535)."""

# Execution and ordering
ExecutionOrder = Annotated[int, Field(ge=0)]
"""Non-negative execution order (lower = earlier)."""

Priority = Annotated[int, Field(ge=0, le=100)]
"""Priority level (0-100, higher = more important)."""

# Sampling and percentages
SamplingRate = Annotated[float, Field(ge=0.0, le=1.0)]
"""Sampling rate probability (0.0-1.0)."""

Percentage = Annotated[float, Field(ge=0.0, le=100.0)]
"""Percentage value (0-100)."""

# Time durations (numeric)
TimeoutSeconds = Annotated[float, Field(gt=0)]
"""Timeout duration in seconds (must be positive)."""

IntervalSeconds = Annotated[float, Field(gt=0)]
"""Interval in seconds (must be positive)."""

# Counts and sizes
# Note: PositiveInt, NonNegativeInt, PositiveFloat, NonNegativeFloat are imported from pydantic
# and re-exported for backward compatibility. They use identical constraints (gt=0, ge=0).

ByteSize = Annotated[int, Field(ge=0)]
"""Size in bytes (non-negative)."""

# Decimal types for precise measurements (not available in Pydantic natively)
PositiveDecimal = Annotated[Decimal, Field(gt=0)]
"""Positive decimal number (>0) for precise measurements like benchmarks, rates."""

FinitePositiveDecimal = Annotated[Decimal, Field(gt=0, allow_inf_nan=False)]
"""Finite positive decimal (>0, no inf/NaN) for benchmark metrics and measurements."""

# TODO: Currently unused - consider removal or document intended use
NonNegativeDecimal = Annotated[Decimal, Field(ge=0)]
"""Non-negative decimal (>=0) for optional precise measurements."""

# Exit codes (Unix/POSIX conventions)
ExitCode = Annotated[int, Field(ge=0, le=255)]
"""Process exit code (0-255) following Unix/POSIX conventions."""


# -----------------------------------------------------------------------------
# Path Types (Strict Validation)
# -----------------------------------------------------------------------------

# TODO: Currently unused - consider removal or document intended use
StrictFilePath = FilePath
"""Path that must exist and be a file. Use when file existence validation is required."""

# TODO: Currently unused - consider removal or document intended use
StrictDirectoryPath = DirectoryPath
"""Path that must exist and be a directory. Use when directory existence validation is required."""


# -----------------------------------------------------------------------------
# Strict Validation Types
# -----------------------------------------------------------------------------

STRICT_CONTEXT_KEY = "strict_models"


def _ensure_strict_bool(value: Any, info: ValidationInfo) -> Any:
    """Enforce boolean type when strict_models context is enabled.

    In non-strict mode, allows Pydantic's default coercion (e.g., 1 -> True).
    In strict mode, rejects non-boolean values.
    """
    if value is None:
        return value
    # Check if strict mode is enabled via validation context
    if info.context and info.context.get(STRICT_CONTEXT_KEY):
        if not isinstance(value, bool):
            raise TypeError(
                f"{info.field_name or 'field'} must be a boolean when strict models are enabled"
            )
    return value


StrictBool = Annotated[bool | None, BeforeValidator(_ensure_strict_bool)]
"""Boolean field with strict type checking when strict_models context is enabled."""


# -----------------------------------------------------------------------------
# Additional Semantic String Types
# -----------------------------------------------------------------------------

# State machine identifiers
StateName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z_][a-z0-9_]*$", min_length=1, max_length=64),
]
"""State machine state name in snake_case (e.g., 'idle', 'processing', 'error_state')."""

# CLI command names
CommandName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", min_length=1, max_length=64),
]
"""CLI command name in kebab-case (e.g., 'run', 'list-files', 'generate-report')."""

# Data format identifiers
FormatName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", min_length=1, max_length=32),
]
"""Data format name in lowercase (e.g., 'json', 'msgpack', 'parquet', 'arrow-ipc')."""

# Configuration keys
ConfigKey = Annotated[
    str,
    StringConstraints(pattern=r"^[a-z][a-z0-9._]*$", min_length=1, max_length=128),
]
"""Configuration key in dotted notation (e.g., 'database.host', 'logging.level')."""

# Exception type names
ExceptionTypeName = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Z][a-zA-Z0-9]*$", min_length=1),
]
"""Exception type name in PascalCase (e.g., 'ValueError', 'ConnectionError')."""


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


class EntityMaturity(str, Enum):
    """Development maturity stage of an entity.

    Universal progression tracking for types, functions, features, and methods.
    This is the single source of truth for "how developed is this entity?"

    Stages represent increasing maturity:
    - idea: Rough concept, may change significantly
    - specified: Behavior described, acceptance criteria clear
    - designed: Shape defined (signatures, contracts, types)
    - implemented: Code exists
    - tested: Tests exist and pass
    - documented: User-facing docs exist
    - released: Part of a public release
    - deprecated: Marked for removal
    """

    IDEA = "idea"
    SPECIFIED = "specified"
    DESIGNED = "designed"
    IMPLEMENTED = "implemented"
    TESTED = "tested"
    DOCUMENTED = "documented"
    RELEASED = "released"
    DEPRECATED = "deprecated"


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
    ML = "ml"  # PLANNED: Not yet implemented - ML-specific fields pending design
    SERIALIZATION = "serialization"

    # Concern extensions
    ERRORS = "errors"
    PERF = "perf"
    SAFETY = "safety"
    CONFIG = "config"
    VERSIONING = "versioning"
    OBSERVABILITY = "observability"
    WORKFLOW = "workflow"


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
