"""Python version constants and utilities for tracking typing features.

This module provides mappings from typing features to the Python versions
where they were introduced, enabling version-aware validation and lint rules.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

# Mapping of typing features to the Python version where they were introduced
TYPING_FEATURES: dict[str, str] = {
    # PEP 484 (Python 3.5+) - Core typing
    "TypeVar": "3.8",  # Base support since 3.5, but we track from 3.8
    "Generic": "3.8",
    "Optional": "3.8",
    "Union": "3.8",
    "Callable": "3.8",
    "List": "3.8",
    "Dict": "3.8",
    "Set": "3.8",
    "Tuple": "3.8",
    "Type": "3.8",
    "Any": "3.8",
    "ClassVar": "3.8",
    # PEP 544 (Python 3.8) - Protocols
    "Protocol": "3.8",
    "runtime_checkable": "3.8",
    # PEP 586 (Python 3.8) - Literal types
    "Literal": "3.8",
    # PEP 589 (Python 3.8) - TypedDict
    "TypedDict": "3.8",
    "Required": "3.11",  # PEP 655
    "NotRequired": "3.11",  # PEP 655
    "ReadOnly": "3.13",  # PEP 705
    # PEP 591 (Python 3.8) - Final
    "Final": "3.8",
    "final": "3.8",
    # PEP 593 (Python 3.9) - Annotated
    "Annotated": "3.9",
    # PEP 604 (Python 3.10) - Union syntax X | Y
    # Note: This is syntax, not a name, detected separately
    # PEP 612 (Python 3.10) - ParamSpec
    "ParamSpec": "3.10",
    "Concatenate": "3.10",
    # PEP 613 (Python 3.10) - TypeAlias
    "TypeAlias": "3.10",
    # PEP 647 (Python 3.10) - TypeGuard
    "TypeGuard": "3.10",
    # PEP 646 (Python 3.11) - TypeVarTuple
    "TypeVarTuple": "3.11",
    "Unpack": "3.11",
    # PEP 654 (Python 3.11) - Exception Groups
    "BaseExceptionGroup": "3.11",
    "ExceptionGroup": "3.11",
    # PEP 673 (Python 3.11) - Self type
    "Self": "3.11",
    # PEP 675 (Python 3.11) - LiteralString
    "LiteralString": "3.11",
    # PEP 681 (Python 3.11) - dataclass_transform
    "dataclass_transform": "3.11",
    # PEP 655 (Python 3.11) - Required/NotRequired for TypedDict
    # Already listed above
    # PEP 698 (Python 3.12) - Override
    "override": "3.12",
    # PEP 695 (Python 3.12) - Type parameter syntax
    # Note: `type X = ...` syntax detected separately
    # PEP 702 (Python 3.13) - Deprecation
    "deprecated": "3.13",
    # PEP 742 (Python 3.13) - TypeIs
    "TypeIs": "3.13",
    # PEP 728 (Python 3.13) - Closed TypedDict
    # Note: `closed=True` in TypedDict detected separately
    # PEP 705 (Python 3.13) - ReadOnly for TypedDict
    # Already listed above
    # Python 3.14+ features (preview/planned)
    "TypeForm": "3.14",  # PEP 747
}

# Type annotation syntax patterns introduced in specific Python versions
SYNTAX_PATTERNS: dict[str, tuple[str, str]] = {
    # Pattern: (python_version, description)
    r"\|": ("3.10", "Union syntax (X | Y)"),
    r"\btype\s+\w+\s*=": ("3.12", "Type alias syntax (type X = ...)"),
    r"\[\s*\*\w+\s*\]": ("3.11", "TypeVarTuple unpacking ([*Ts])"),
    r"tuple\[.*\*\w+": ("3.11", "TypeVarTuple in tuple unpacking"),
}


def detect_type_features(signature: str) -> Iterator[tuple[str, str, str]]:
    """Detect version-specific typing features in a signature.

    Args:
        signature: A type signature or annotation string.

    Yields:
        Tuples of (feature_name, python_version, context).
    """
    # Check for named typing features
    for feature, version in TYPING_FEATURES.items():
        # Use word boundary to avoid partial matches
        pattern = rf"\b{re.escape(feature)}\b"
        if re.search(pattern, signature):
            yield (feature, version, f"Uses {feature}")

    # Check for syntax patterns
    for pattern, (version, description) in SYNTAX_PATTERNS.items():
        if re.search(pattern, signature):
            yield (description, version, description)


def extract_min_python_version(features: list[tuple[str, str, str]]) -> str | None:
    """Extract the minimum Python version required for a set of features.

    Args:
        features: List of (feature_name, python_version, context) tuples.

    Returns:
        The highest required Python version, or None if no features detected.
    """
    if not features:
        return None

    versions = [f[1] for f in features]

    def version_key(v: str) -> tuple[int, int]:
        parts = v.replace("+", "").split(".")
        return (int(parts[0]), int(parts[1]))

    return max(versions, key=version_key)


def parse_python_requires(spec: str) -> str | None:
    """Extract minimum Python version from a python_requires specifier.

    Args:
        spec: A PEP 440 version specifier (e.g., '>=3.10', '>=3.10,<4.0').

    Returns:
        The minimum version as a string (e.g., '3.10'), or None if not parseable.
    """
    # Match patterns like >=3.10, >=3.10.0, ~=3.10
    match = re.search(r">=\s*(\d+\.\d+)", spec)
    if match:
        return match.group(1)

    # Match ~= (compatible release)
    match = re.search(r"~=\s*(\d+\.\d+)", spec)
    if match:
        return match.group(1)

    return None


def version_compare(v1: str, v2: str) -> int:
    """Compare two Python version strings.

    Args:
        v1: First version string (e.g., '3.10').
        v2: Second version string (e.g., '3.11').

    Returns:
        -1 if v1 < v2, 0 if v1 == v2, 1 if v1 > v2.
    """

    def to_tuple(v: str) -> tuple[int, int]:
        parts = v.replace("+", "").split(".")
        return (int(parts[0]), int(parts[1]))

    t1, t2 = to_tuple(v1), to_tuple(v2)
    if t1 < t2:
        return -1
    elif t1 > t2:
        return 1
    return 0


# Mapping of typing features to typing_extensions backport availability
# Format: feature -> (stdlib_version, typing_extensions_version)
TYPING_EXTENSIONS_BACKPORTS: dict[str, tuple[str, str]] = {
    # PEP 544 (Protocols) - available in typing_extensions since early versions
    "Protocol": ("3.8", "3.7"),
    "runtime_checkable": ("3.8", "3.7"),
    # PEP 586 (Literal)
    "Literal": ("3.8", "3.7"),
    # PEP 589 (TypedDict)
    "TypedDict": ("3.8", "3.7"),
    # PEP 591 (Final)
    "Final": ("3.8", "3.7"),
    "final": ("3.8", "3.7"),
    # PEP 593 (Annotated)
    "Annotated": ("3.9", "3.7"),
    # PEP 612 (ParamSpec)
    "ParamSpec": ("3.10", "3.10"),
    "Concatenate": ("3.10", "3.10"),
    # PEP 613 (TypeAlias)
    "TypeAlias": ("3.10", "3.10"),
    # PEP 647 (TypeGuard)
    "TypeGuard": ("3.10", "3.10"),
    # PEP 646 (TypeVarTuple)
    "TypeVarTuple": ("3.11", "4.0"),
    "Unpack": ("3.11", "4.0"),
    # PEP 655 (Required/NotRequired for TypedDict)
    "Required": ("3.11", "4.0"),
    "NotRequired": ("3.11", "4.0"),
    # PEP 673 (Self)
    "Self": ("3.11", "4.0"),
    # PEP 675 (LiteralString)
    "LiteralString": ("3.11", "4.0"),
    # PEP 681 (dataclass_transform)
    "dataclass_transform": ("3.11", "4.1"),
    # PEP 698 (override)
    "override": ("3.12", "4.4"),
    # PEP 702 (deprecated)
    "deprecated": ("3.13", "4.5"),
    # PEP 705 (ReadOnly)
    "ReadOnly": ("3.13", "4.9"),
    # PEP 742 (TypeIs)
    "TypeIs": ("3.13", "4.10"),
}


# Deprecated typing patterns that can be modernized
# Format: (regex_pattern, old_style, new_style, deprecated_since_version)
DEPRECATED_PATTERNS: list[tuple[str, str, str, str]] = [
    # PEP 585 (Python 3.9) - Generic types can use built-in syntax
    (r"\bList\[", "List[T]", "list[T]", "3.9"),
    (r"\bDict\[", "Dict[K, V]", "dict[K, V]", "3.9"),
    (r"\bSet\[", "Set[T]", "set[T]", "3.9"),
    (r"\bFrozenSet\[", "FrozenSet[T]", "frozenset[T]", "3.9"),
    (r"\bTuple\[", "Tuple[T, ...]", "tuple[T, ...]", "3.9"),
    (r"\bType\[", "Type[C]", "type[C]", "3.9"),
    # PEP 604 (Python 3.10) - Union syntax
    (r"\bOptional\[", "Optional[X]", "X | None", "3.10"),
    (r"\bUnion\[", "Union[X, Y]", "X | Y", "3.10"),
]


def is_version_compatible(
    feature_version: str, library_requires: str | None
) -> bool:
    """Check if a feature version is compatible with library requirements.

    Args:
        feature_version: Python version when feature was introduced (e.g., '3.11').
        library_requires: Library's python_requires specifier (e.g., '>=3.10').

    Returns:
        True if the feature is compatible (library requires >= feature version).
    """
    if library_requires is None:
        return True  # No constraint means we assume compatibility

    min_version = parse_python_requires(library_requires)
    if min_version is None:
        return True  # Can't parse, assume compatible

    return version_compare(min_version, feature_version) >= 0
