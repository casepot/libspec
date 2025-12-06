"""Codegen command: Generate Python stubs from libspec.json specifications.

This module provides the `codegen` CLI command for generating:
- Function stubs with full signatures, type hints, and rich docstrings
- Type definitions (dataclasses, enums, classes) with properties and methods
- Test scaffolding from feature verification steps
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import click

from libspec.cli.app import Context, pass_context

# === Constants ===

# Regex to parse function signatures like:
# (repo_path: str, project_id: str | None = None) -> RegisterProjectResult
SIGNATURE_PATTERN = re.compile(
    r"^\((?P<params>.*?)\)\s*(?:->\s*(?P<returns>.+))?$",
    re.DOTALL,
)

# Pattern for Optional[X] -> X | None conversion
OPTIONAL_PATTERN = re.compile(r"Optional\[([^\]]+)\]")

# Parse individual parameter: name: type = default
PARAM_PATTERN = re.compile(
    r"^(?P<name>\w+)\s*:\s*(?P<type>[^=]+?)(?:\s*=\s*(?P<default>.+))?$"
)

# Known stdlib type imports (pattern -> import statement)
# Patterns use word boundaries to avoid false matches
STDLIB_TYPE_IMPORTS: dict[str, str] = {
    # datetime module
    r"\bdatetime\b": "from datetime import datetime",
    r"\bdate\b": "from datetime import date",
    r"\btimedelta\b": "from datetime import timedelta",
    r"\btimezone\b": "from datetime import timezone",
    # pathlib
    r"\bPath\b": "from pathlib import Path",
    # decimal
    r"\bDecimal\b": "from decimal import Decimal",
    # uuid
    r"\bUUID\b": "from uuid import UUID",
    # re
    r"\bPattern\b": "from re import Pattern",
    r"\bMatch\b": "from re import Match",
    # typing - generics and protocols
    r"\bCallable\b": "from collections.abc import Callable",
    r"\bAwaitable\b": "from collections.abc import Awaitable",
    r"\bAsyncIterator\b": "from collections.abc import AsyncIterator",
    r"\bAsyncGenerator\b": "from collections.abc import AsyncGenerator",
    r"\bIterator\b": "from collections.abc import Iterator",
    r"\bGenerator\b": "from collections.abc import Generator",
    r"\bSequence\b": "from collections.abc import Sequence",
    r"\bMapping\b": "from collections.abc import Mapping",
    r"\bMutableMapping\b": "from collections.abc import MutableMapping",
    r"\bIterable\b": "from collections.abc import Iterable",
    r"\bCoroutine\b": "from collections.abc import Coroutine",
    # typing - special forms
    r"\bLiteral\b": "from typing import Literal",
    r"\bTypeVar\b": "from typing import TypeVar",
    r"\bParamSpec\b": "from typing import ParamSpec",
    r"\bTypeVarTuple\b": "from typing import TypeVarTuple",
    r"\bGeneric\b": "from typing import Generic",
    r"\bClassVar\b": "from typing import ClassVar",
    r"\bFinal\b": "from typing import Final",
    r"\bTypeAlias\b": "from typing import TypeAlias",
    r"\bSelf\b": "from typing import Self",
    r"\bNever\b": "from typing import Never",
    r"\bNoReturn\b": "from typing import NoReturn",
    r"\bUnpack\b": "from typing import Unpack",
    r"\bConcatenate\b": "from typing import Concatenate",
    # contextlib
    r"\bContextManager\b": "from contextlib import AbstractContextManager as ContextManager",
    r"\bAsyncContextManager\b": "from contextlib import AbstractAsyncContextManager as AsyncContextManager",
}

# Known base class imports for inheritance resolution
# Maps base class names to their import statements (None = builtin, no import needed)
KNOWN_BASE_IMPORTS: dict[str, str | None] = {
    # typing
    "Protocol": "from typing import Protocol",
    "Generic": "from typing import Generic",
    # abc
    "ABC": "from abc import ABC",
    # pydantic
    "BaseModel": "from pydantic import BaseModel",
    "RootModel": "from pydantic import RootModel",
    "BaseSettings": "from pydantic_settings import BaseSettings",
    # builtins (no import needed)
    "Exception": None,
    "BaseException": None,
    "ValueError": None,
    "TypeError": None,
    "RuntimeError": None,
    "KeyError": None,
    "AttributeError": None,
    "NotImplementedError": None,
    "StopIteration": None,
    "StopAsyncIteration": None,
    "object": None,
    # enum
    "Enum": "from enum import Enum",
    "IntEnum": "from enum import IntEnum",
    "StrEnum": "from enum import StrEnum",
    "Flag": "from enum import Flag",
    "IntFlag": "from enum import IntFlag",
}

# Known stdlib decorator imports for auto-inference
STDLIB_DECORATOR_IMPORTS: dict[str, str] = {
    # functools
    "lru_cache": "functools",
    "cache": "functools",
    "cached_property": "functools",
    "wraps": "functools",
    "total_ordering": "functools",
    "singledispatch": "functools",
    "singledispatchmethod": "functools",
    # contextlib
    "contextmanager": "contextlib",
    "asynccontextmanager": "contextlib",
    # abc
    "abstractmethod": "abc",
    "abstractproperty": "abc",
    # dataclasses
    "dataclass": "dataclasses",
    # typing
    "overload": "typing",
    "final": "typing",
    "runtime_checkable": "typing",
    # atexit
    "atexit.register": "atexit",
}


# === Data Models ===


@dataclass
class ParsedParam:
    """A parsed function parameter."""

    name: str
    type_hint: str
    default: str | None = None
    kind: str = "positional_or_keyword"


@dataclass
class ParsedSignature:
    """A parsed function signature."""

    params: list[ParsedParam]
    returns: str | None


@dataclass
class ModuleContent:
    """Content to generate for a single module."""

    functions: list[dict] = field(default_factory=list)
    types: list[dict] = field(default_factory=list)


@dataclass
class GenerationResult:
    """Result of code generation."""

    module: str
    code: str
    path: Path | None = None


# === Type Normalization ===


def normalize_type(type_str: str) -> str:
    """Convert type annotations to modern Python 3.10+ syntax.

    Converts:
    - Optional[X] -> X | None
    - List[X] -> list[X]
    - Dict[K, V] -> dict[K, V]
    """
    if not type_str:
        return type_str

    result = type_str

    # Convert Optional[X] to X | None
    while OPTIONAL_PATTERN.search(result):
        result = OPTIONAL_PATTERN.sub(r"\1 | None", result)

    # Convert List -> list, Dict -> dict, etc.
    result = re.sub(r"\bList\[", "list[", result)
    result = re.sub(r"\bDict\[", "dict[", result)
    result = re.sub(r"\bTuple\[", "tuple[", result)
    result = re.sub(r"\bSet\[", "set[", result)
    result = re.sub(r"\bFrozenSet\[", "frozenset[", result)

    return result


# === Signature Parsing ===


def parse_signature(sig: str) -> ParsedSignature:
    """Parse a function signature string into components."""
    sig = sig.strip()
    match = SIGNATURE_PATTERN.match(sig)
    if not match:
        return ParsedSignature(params=[], returns=None)

    params_str = match.group("params").strip()
    returns = match.group("returns")
    if returns:
        returns = normalize_type(returns.strip())

    params = []
    if params_str:
        # Split on commas not inside brackets
        depth = 0
        current: list[str] = []
        for char in params_str + ",":
            if char in "([{":
                depth += 1
                current.append(char)
            elif char in ")]}":
                depth -= 1
                current.append(char)
            elif char == "," and depth == 0:
                param_str = "".join(current).strip()
                if param_str:
                    param = parse_param(param_str)
                    if param:
                        params.append(param)
                current = []
            else:
                current.append(char)

    return ParsedSignature(params=params, returns=returns)


def parse_param(param_str: str) -> ParsedParam | None:
    """Parse a single parameter string."""
    match = PARAM_PATTERN.match(param_str.strip())
    if not match:
        return None

    return ParsedParam(
        name=match.group("name"),
        type_hint=normalize_type(match.group("type").strip()),
        default=match.group("default").strip() if match.group("default") else None,
    )


# === Docstring Rendering ===


def render_function_docstring(func: dict, spec: dict | None = None) -> str:
    """Render docstring for a function from libspec data."""
    lines = [func.get("description", "")]

    # Add maturity status
    maturity = func.get("maturity")
    if maturity:
        lines.append("")
        lines.append(f"Status: {maturity}")

    # Add function kind for special function types
    func_kind = func.get("kind")
    if func_kind in ("decorator", "context_manager", "async_context_manager"):
        lines.append("")
        lines.append(f"Kind: {func_kind.replace('_', ' ')}")

    params = func.get("parameters", [])
    if params:
        lines.append("")
        lines.append("Args:")
        for p in params:
            kind_str = ""
            p_kind = p.get("kind", "positional_or_keyword")
            if p_kind == "keyword_only":
                kind_str = " (keyword-only)"
            elif p_kind == "positional_only":
                kind_str = " (positional-only)"

            default_str = ""
            if p.get("default") and p["default"] != "REQUIRED":
                default_str = f" (default: {p['default']})"
            lines.append(
                f"    {p['name']}{kind_str}: {p.get('description', '')}{default_str}"
            )

    returns = func.get("returns")
    if returns:
        lines.append("")
        lines.append("Returns:")
        lines.append(f"    {returns.get('description', returns.get('type', ''))}")

    yields = func.get("yields")
    if yields:
        lines.append("")
        lines.append("Yields:")
        yield_type = yields.get("type", "")
        yield_desc = yields.get("description", "")
        if yield_type and yield_desc:
            lines.append(f"    {yield_type}: {yield_desc}")
        elif yield_desc:
            lines.append(f"    {yield_desc}")
        elif yield_type:
            lines.append(f"    {yield_type}")

    raises = func.get("raises", [])
    if raises:
        lines.append("")
        lines.append("Raises:")
        for r in raises:
            lines.append(f"    {r['type']}: {r.get('when', '')}")

    preconditions = func.get("preconditions", [])
    if preconditions:
        lines.append("")
        lines.append("Preconditions:")
        for p in preconditions:
            lines.append(f"    - {p}")

    postconditions = func.get("postconditions", [])
    if postconditions:
        lines.append("")
        lines.append("Postconditions:")
        for p in postconditions:
            lines.append(f"    - {p}")

    invariants = func.get("invariants", [])
    if invariants:
        lines.append("")
        lines.append("Invariants:")
        for i in invariants:
            lines.append(f"    - {i}")

    # Properties
    props = []
    if func.get("pure"):
        props.append("This function is pure (no side effects).")
    if func.get("deterministic"):
        props.append("This function is deterministic.")
    if func.get("idempotent"):
        props.append("This function is idempotent.")
    if props:
        lines.append("")
        lines.append("Note:")
        for p in props:
            lines.append(f"    {p}")

    example = func.get("example")
    if example:
        lines.append("")
        lines.append("Example:")
        lines.append(f"    >>> {example}")

    related = func.get("related", [])
    if related:
        lines.append("")
        lines.append("See Also:")
        for r in related:
            lines.append(f"    - {r}")

    return "\n".join(lines)


def render_type_docstring(typ: dict) -> str:
    """Render docstring for a type from libspec data."""
    lines = [typ.get("docstring", "")]

    maturity = typ.get("maturity")
    if maturity:
        lines.append("")
        lines.append(f"Status: {maturity}")

    kind = typ.get("kind", "")
    values = typ.get("values", [])
    if kind == "enum" and values:
        lines.append("")
        lines.append("Values:")
        for v in values:
            desc = v.get("description", "")
            val = v.get("value", "")
            suffix = f" ({val})" if val else ""
            lines.append(f"    {v['name']}: {desc}{suffix}")

    properties = typ.get("properties", [])
    if properties:
        lines.append("")
        lines.append("Attributes:")
        for p in properties:
            constraints_str = ""
            if p.get("constraints"):
                const_parts = [f"{k}={v}" for k, v in p["constraints"].items()]
                constraints_str = f" (range: {', '.join(const_parts)})"

            default_str = ""
            if p.get("default"):
                default_str = f" (default: {p['default']})"
            lines.append(
                f"    {p['name']} ({p.get('type', 'Any')}): {p.get('description', '')}{constraints_str}{default_str}"
            )

    invariants = typ.get("invariants", [])
    if invariants:
        lines.append("")
        lines.append("Invariants:")
        for i in invariants:
            lines.append(f"    - {i}")

    related = typ.get("related", [])
    if related:
        lines.append("")
        lines.append("See Also:")
        for r in related:
            lines.append(f"    - {r}")

    example = typ.get("example")
    if example:
        lines.append("")
        lines.append("Example:")
        lines.append(f"    >>> {example}")

    return "\n".join(lines)


# === AST Code Generation ===


def make_type_annotation(type_str: str) -> ast.expr:
    """Create an AST node for a type annotation string."""
    try:
        node = ast.parse(type_str, mode="eval").body
        return node
    except SyntaxError:
        return ast.Constant(value=type_str)


def generate_decorator_ast(decorator: str | dict) -> ast.expr:
    """Generate AST for a decorator from libspec DecoratorSpec.

    Args:
        decorator: Either a simple string name or a DecoratorSpec dict with:
            - name: Decorator name (may be dotted like 'mcp.tool')
            - args: Positional arguments as Python expression strings
            - kwargs: Keyword arguments as name -> Python expression mapping
            - call: Whether to call the decorator (default True)

    Returns:
        AST expression for the decorator.
    """
    if isinstance(decorator, str):
        # Simple decorator name
        return _make_name_or_attribute(decorator)

    # DecoratorSpec dict
    name = decorator.get("name", "")
    args = decorator.get("args", [])
    kwargs = decorator.get("kwargs", {})
    call = decorator.get("call", True)

    # Build the decorator name (may be dotted)
    name_node = _make_name_or_attribute(name)

    # If no args/kwargs and call is False, just return the name
    if not args and not kwargs and not call:
        return name_node

    # If no args/kwargs but call is True (default), return name()
    if not args and not kwargs:
        return ast.Call(func=name_node, args=[], keywords=[])

    # Build call with args and kwargs
    arg_nodes = []
    for arg in args:
        try:
            arg_nodes.append(ast.parse(arg, mode="eval").body)
        except SyntaxError:
            arg_nodes.append(ast.Constant(value=arg))

    kwarg_nodes = []
    for key, value in kwargs.items():
        try:
            value_node = ast.parse(value, mode="eval").body
        except SyntaxError:
            value_node = ast.Constant(value=value)
        kwarg_nodes.append(ast.keyword(arg=key, value=value_node))

    return ast.Call(func=name_node, args=arg_nodes, keywords=kwarg_nodes)


def _make_name_or_attribute(dotted_name: str) -> ast.expr:
    """Create Name or Attribute node for a potentially dotted name."""
    parts = dotted_name.split(".")
    if len(parts) == 1:
        return ast.Name(id=parts[0], ctx=ast.Load())

    # Build nested Attribute nodes
    result: ast.expr = ast.Name(id=parts[0], ctx=ast.Load())
    for part in parts[1:]:
        result = ast.Attribute(value=result, attr=part, ctx=ast.Load())
    return result


def generate_function_ast(
    func: dict,
    is_method: bool = False,
    method_type: str = "instance",
    spec: dict | None = None,
) -> ast.FunctionDef | ast.AsyncFunctionDef:
    """Build AST for a function stub."""
    name = func["name"]
    sig_str = func.get("signature", "()")
    sig = parse_signature(sig_str)

    func_kind = func.get("kind", "function")

    # Build arguments
    posonlyargs: list[ast.arg] = []
    args_list: list[ast.arg] = []
    kwonlyargs: list[ast.arg] = []
    defaults: list[ast.expr] = []
    kw_defaults: list[ast.expr | None] = []

    if is_method:
        if method_type == "classmethod":
            args_list.append(ast.arg(arg="cls", annotation=None))
        elif method_type == "staticmethod":
            pass
        else:
            args_list.append(ast.arg(arg="self", annotation=None))

    libspec_params = func.get("parameters", [])
    param_kind_map = {
        p.get("name"): p.get("kind", "positional_or_keyword") for p in libspec_params
    }

    for p in sig.params:
        arg = ast.arg(arg=p.name, annotation=make_type_annotation(p.type_hint))
        kind = param_kind_map.get(p.name, "positional_or_keyword")

        default_node = None
        if p.default is not None:
            try:
                default_node = ast.parse(p.default, mode="eval").body
            except SyntaxError:
                default_node = ast.Constant(value=p.default)

        if kind == "positional_only":
            posonlyargs.append(arg)
            if default_node is not None:
                defaults.append(default_node)
        elif kind == "keyword_only":
            kwonlyargs.append(arg)
            kw_defaults.append(default_node)
        else:
            args_list.append(arg)
            if default_node is not None:
                defaults.append(default_node)

    arguments = ast.arguments(
        posonlyargs=posonlyargs,
        args=args_list,
        vararg=None,
        kwonlyargs=kwonlyargs,
        kw_defaults=kw_defaults,
        kwarg=None,
        defaults=defaults,
    )

    returns_node = None
    if sig.returns:
        returns_node = make_type_annotation(sig.returns)

    docstring = render_function_docstring(func, spec)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
        ast.Raise(
            exc=ast.Call(
                func=ast.Name(id="NotImplementedError", ctx=ast.Load()),
                args=[ast.Constant(value=f"{name} not implemented")],
                keywords=[],
            ),
            cause=None,
        ),
    ]

    # Build decorator list
    decorators: list[ast.expr] = []

    # Add method type decorators first
    if is_method:
        if method_type == "classmethod":
            decorators.append(ast.Name(id="classmethod", ctx=ast.Load()))
        elif method_type == "staticmethod":
            decorators.append(ast.Name(id="staticmethod", ctx=ast.Load()))

    # Add function kind decorators
    if func_kind == "context_manager":
        decorators.append(ast.Name(id="contextmanager", ctx=ast.Load()))
    elif func_kind == "async_context_manager":
        decorators.append(ast.Name(id="asynccontextmanager", ctx=ast.Load()))

    # Add decorators from libspec
    for dec in func.get("decorators", []):
        decorators.append(generate_decorator_ast(dec))

    # Use AsyncFunctionDef for async functions
    if func_kind == "async_context_manager":
        return ast.AsyncFunctionDef(
            name=name,
            args=arguments,
            body=body,
            decorator_list=decorators,
            returns=returns_node,
            type_params=[],
        )

    return ast.FunctionDef(
        name=name,
        args=arguments,
        body=body,
        decorator_list=decorators,
        returns=returns_node,
        type_params=[],
    )


def generate_enum_ast(typ: dict, use_pydantic: bool = False) -> ast.ClassDef:
    """Build AST for an enum type."""
    name = typ["name"]
    docstring = render_type_docstring(typ)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
    ]

    for val in typ.get("values", []):
        val_name = val["name"]
        val_value = val.get("value", val_name.lower())
        body.append(
            ast.Assign(
                targets=[ast.Name(id=val_name, ctx=ast.Store())],
                value=ast.Constant(value=val_value),
            )
        )

    if len(body) == 1:
        body.append(ast.Pass())

    if use_pydantic:
        bases: list[ast.expr] = [
            ast.Name(id="str", ctx=ast.Load()),
            ast.Attribute(
                value=ast.Name(id="enum", ctx=ast.Load()),
                attr="Enum",
                ctx=ast.Load(),
            ),
        ]
    else:
        bases = [
            ast.Attribute(
                value=ast.Name(id="enum", ctx=ast.Load()),
                attr="Enum",
                ctx=ast.Load(),
            )
        ]

    return ast.ClassDef(
        name=name,
        bases=bases,
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )


def generate_dataclass_ast(typ: dict) -> ast.ClassDef:
    """Build AST for a dataclass type."""
    name = typ["name"]
    docstring = render_type_docstring(typ)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
    ]

    for prop in typ.get("properties", []):
        prop_name = prop["name"]
        prop_type = normalize_type(prop.get("type", "Any"))
        default = prop.get("default")

        annotation = make_type_annotation(prop_type)

        if default is not None:
            is_list_or_dict = (
                default in ("[]", "{}", "set()")
                or default.startswith("[")
                or default.startswith("{")
            )
            is_constructor_call = (
                re.match(r"^[A-Z][a-zA-Z0-9]*\(\)$", default) is not None
            )
            is_mutable_default = is_list_or_dict or is_constructor_call

            if is_mutable_default:
                if default == "[]" or default.startswith("["):
                    factory = ast.Name(id="list", ctx=ast.Load())
                elif default == "{}" or default.startswith("{"):
                    factory = ast.Name(id="dict", ctx=ast.Load())
                elif default == "set()":
                    factory = ast.Name(id="set", ctx=ast.Load())
                elif is_constructor_call:
                    class_name = default[:-2]
                    factory = ast.Name(id=class_name, ctx=ast.Load())
                else:
                    factory = ast.Name(id="list", ctx=ast.Load())

                default_node = ast.Call(
                    func=ast.Name(id="field", ctx=ast.Load()),
                    args=[],
                    keywords=[ast.keyword(arg="default_factory", value=factory)],
                )
            else:
                try:
                    default_node = ast.parse(default, mode="eval").body
                except SyntaxError:
                    default_node = ast.Constant(value=default)

            body.append(
                ast.AnnAssign(
                    target=ast.Name(id=prop_name, ctx=ast.Store()),
                    annotation=annotation,
                    value=default_node,
                    simple=1,
                )
            )
        else:
            body.append(
                ast.AnnAssign(
                    target=ast.Name(id=prop_name, ctx=ast.Store()),
                    annotation=annotation,
                    value=None,
                    simple=1,
                )
            )

    for method in typ.get("methods", []):
        method_dict = {
            "name": method["name"],
            "signature": method.get("signature", "()"),
            "description": method.get("description", ""),
        }
        body.append(generate_function_ast(method_dict, is_method=True))

    if len(body) == 1:
        body.append(ast.Pass())

    decorator = ast.Name(id="dataclass", ctx=ast.Load())

    bases: list[ast.expr] = [
        ast.Name(id=base, ctx=ast.Load()) for base in typ.get("bases", [])
    ]

    return ast.ClassDef(
        name=name,
        bases=bases,
        keywords=[],
        body=body,
        decorator_list=[decorator],
        type_params=[],
    )


def generate_pydantic_model_ast(typ: dict) -> ast.ClassDef:
    """Build AST for a Pydantic BaseModel type."""
    name = typ["name"]
    docstring = render_type_docstring(typ)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
    ]

    for prop in typ.get("properties", []):
        prop_name = prop["name"]
        prop_type = normalize_type(prop.get("type", "Any"))
        default = prop.get("default")
        description = prop.get("description", "")
        constraints = prop.get("constraints", {})

        annotation = make_type_annotation(prop_type)

        field_keywords: list[ast.keyword] = []

        if default is not None:
            is_mutable = (
                default in ("[]", "{}", "set()")
                or default.startswith("[")
                or default.startswith("{")
                or re.match(r"^[A-Z][a-zA-Z0-9]*\(\)$", default) is not None
            )

            if is_mutable:
                if default == "[]" or default.startswith("["):
                    factory = ast.Name(id="list", ctx=ast.Load())
                elif default == "{}" or default.startswith("{"):
                    factory = ast.Name(id="dict", ctx=ast.Load())
                elif default == "set()":
                    factory = ast.Name(id="set", ctx=ast.Load())
                else:
                    class_name = default[:-2]
                    factory = ast.Name(id=class_name, ctx=ast.Load())
                field_keywords.append(
                    ast.keyword(arg="default_factory", value=factory)
                )
            else:
                try:
                    default_node = ast.parse(default, mode="eval").body
                except SyntaxError:
                    default_node = ast.Constant(value=default)
                field_keywords.append(ast.keyword(arg="default", value=default_node))

        if description:
            field_keywords.append(
                ast.keyword(arg="description", value=ast.Constant(value=description))
            )

        constraint_mapping = {
            "ge": "ge",
            "le": "le",
            "gt": "gt",
            "lt": "lt",
            "min": "ge",
            "max": "le",
            "minLength": "min_length",
            "maxLength": "max_length",
            "pattern": "pattern",
        }
        for libspec_key, pydantic_key in constraint_mapping.items():
            if libspec_key in constraints:
                val = constraints[libspec_key]
                field_keywords.append(
                    ast.keyword(arg=pydantic_key, value=ast.Constant(value=val))
                )

        if field_keywords:
            value_node: ast.expr | None = ast.Call(
                func=ast.Name(id="Field", ctx=ast.Load()),
                args=[],
                keywords=field_keywords,
            )
        elif default is None:
            value_node = ast.Constant(value=...)
        else:
            value_node = None

        body.append(
            ast.AnnAssign(
                target=ast.Name(id=prop_name, ctx=ast.Store()),
                annotation=annotation,
                value=value_node,
                simple=1,
            )
        )

    for method in typ.get("methods", []):
        method_dict = {
            "name": method["name"],
            "signature": method.get("signature", "()"),
            "description": method.get("description", ""),
        }
        body.append(generate_function_ast(method_dict, is_method=True))

    if len(body) == 1:
        body.append(ast.Pass())

    # Use bases from spec, defaulting to BaseModel if none specified
    spec_bases = typ.get("bases", [])
    if spec_bases:
        bases: list[ast.expr] = [
            ast.Name(id=base, ctx=ast.Load()) for base in spec_bases
        ]
    else:
        bases = [ast.Name(id="BaseModel", ctx=ast.Load())]

    return ast.ClassDef(
        name=name,
        bases=bases,
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )


def generate_class_ast(typ: dict) -> ast.ClassDef:
    """Build AST for a regular class type."""
    name = typ["name"]
    docstring = render_type_docstring(typ)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
    ]

    for method in typ.get("methods", []):
        method_dict = {
            "name": method["name"],
            "signature": method.get("signature", "()"),
            "description": method.get("description", ""),
        }
        body.append(generate_function_ast(method_dict, is_method=True))

    if len(body) == 1:
        body.append(ast.Pass())

    bases: list[ast.expr] = [
        ast.Name(id=base, ctx=ast.Load()) for base in typ.get("bases", [])
    ]

    return ast.ClassDef(
        name=name,
        bases=bases,
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )


def generate_protocol_ast(typ: dict) -> ast.ClassDef:
    """Build AST for a Protocol type."""
    name = typ["name"]
    docstring = render_type_docstring(typ)

    body: list[ast.stmt] = [
        ast.Expr(value=ast.Constant(value=docstring)),
    ]

    for method in typ.get("methods", []):
        method_dict = {
            "name": method["name"],
            "signature": method.get("signature", "()"),
            "description": method.get("description", ""),
        }
        body.append(generate_function_ast(method_dict, is_method=True))

    if len(body) == 1:
        body.append(ast.Pass())

    bases: list[ast.expr] = [ast.Name(id="Protocol", ctx=ast.Load())]
    for base in typ.get("bases", []):
        bases.append(ast.Name(id=base, ctx=ast.Load()))

    return ast.ClassDef(
        name=name,
        bases=bases,
        keywords=[],
        body=body,
        decorator_list=[],
        type_params=[],
    )


def generate_type_alias_ast(typ: dict) -> ast.Assign:
    """Build AST for a type alias."""
    name = typ["name"]
    target_type = typ.get("target", "Any")

    return ast.Assign(
        targets=[ast.Name(id=name, ctx=ast.Store())],
        value=make_type_annotation(target_type),
    )


# Pydantic base classes that should trigger pydantic model generation
PYDANTIC_BASE_CLASSES = {"BaseModel", "RootModel", "BaseSettings"}


def generate_type_ast(
    typ: dict,
    use_pydantic: bool = False,
) -> ast.ClassDef | ast.Assign:
    """Build AST for a type based on its kind."""
    kind = typ.get("kind", "class")
    bases = set(typ.get("bases", []))

    if kind == "enum":
        return generate_enum_ast(typ, use_pydantic)
    elif kind == "dataclass":
        # Check if bases include a Pydantic base class - if so, use Pydantic model
        # generation regardless of use_pydantic flag (to avoid mixed @dataclass/BaseModel)
        has_pydantic_base = bool(bases & PYDANTIC_BASE_CLASSES)
        if use_pydantic or has_pydantic_base:
            return generate_pydantic_model_ast(typ)
        return generate_dataclass_ast(typ)
    elif kind == "protocol":
        return generate_protocol_ast(typ)
    elif kind == "type_alias":
        return generate_type_alias_ast(typ)
    else:
        return generate_class_ast(typ)


# === Module Generation ===


def group_by_module(
    spec: dict,
    skip_maturity: set[str] | None = None,
) -> dict[str, ModuleContent]:
    """Group functions and types by their target module."""
    modules: dict[str, ModuleContent] = defaultdict(ModuleContent)
    skip = skip_maturity or set()

    library = spec.get("library", {})

    for func in library.get("functions", []):
        if func.get("maturity") in skip:
            continue
        mod = func.get("module", "main")
        modules[mod].functions.append(func)

    for typ in library.get("types", []):
        if typ.get("maturity") in skip:
            continue
        mod = typ.get("module", "main")
        modules[mod].types.append(typ)

    return dict(modules)


def build_type_module_map(spec: dict) -> dict[str, str]:
    """Build a map of type names to their module paths."""
    type_map = {}
    for typ in spec.get("library", {}).get("types", []):
        name = typ.get("name")
        module = typ.get("module")
        if name and module:
            type_map[name] = module
    return type_map


def collect_imports(
    content: ModuleContent,
    type_module_map: dict[str, str] | None = None,
    current_module: str = "",
    use_pydantic: bool = False,
) -> list[str]:
    """Determine required imports for a module."""
    imports = set()

    imports.add("from __future__ import annotations")

    has_dataclass = any(t.get("kind") == "dataclass" for t in content.types)

    if use_pydantic and has_dataclass:
        needs_field = False
        for typ in content.types:
            if typ.get("kind") == "enum":
                continue
            for prop in typ.get("properties", []):
                if prop.get("description") or prop.get("constraints"):
                    needs_field = True
                    break
                default = prop.get("default", "")
                if (
                    default in ("[]", "{}", "set()")
                    or default.startswith("[")
                    or default.startswith("{")
                ):
                    needs_field = True
                    break
            if needs_field:
                break

        if needs_field:
            imports.add("from pydantic import BaseModel, Field")
        else:
            imports.add("from pydantic import BaseModel")

    elif has_dataclass:
        needs_field = False
        for typ in content.types:
            if typ.get("kind") != "dataclass":
                continue
            for prop in typ.get("properties", []):
                default = prop.get("default", "")
                if (
                    default in ("[]", "{}", "set()")
                    or default.startswith("[")
                    or default.startswith("{")
                ):
                    needs_field = True
                    break
                if re.match(r"^[A-Z][a-zA-Z0-9]*\(\)$", default):
                    needs_field = True
                    break
            if needs_field:
                break

        if needs_field:
            imports.add("from dataclasses import dataclass, field")
        else:
            imports.add("from dataclasses import dataclass")

    has_enum = any(t.get("kind") == "enum" for t in content.types)
    if has_enum:
        imports.add("import enum")

    has_context_manager = any(
        f.get("kind") == "context_manager" for f in content.functions
    )
    has_async_context_manager = any(
        f.get("kind") == "async_context_manager" for f in content.functions
    )
    if has_context_manager:
        imports.add("from contextlib import contextmanager")
    if has_async_context_manager:
        imports.add("from contextlib import asynccontextmanager")

    has_protocol = any(t.get("kind") == "protocol" for t in content.types)
    if has_protocol:
        imports.add("from typing import Protocol")

    # Collect imports for generic_params (TypeVar, ParamSpec, TypeVarTuple)
    generic_param_kinds: set[str] = set()
    for typ in content.types:
        for param in typ.get("generic_params", []):
            generic_param_kinds.add(param.get("kind", "type_var"))
    for func in content.functions:
        for param in func.get("generic_params", []):
            generic_param_kinds.add(param.get("kind", "type_var"))

    if "type_var" in generic_param_kinds:
        imports.add("from typing import TypeVar")
    if "param_spec" in generic_param_kinds:
        imports.add("from typing import ParamSpec")
    if "type_var_tuple" in generic_param_kinds:
        imports.add("from typing import TypeVarTuple")

    all_sigs = [f.get("signature", "") for f in content.functions]
    for typ in content.types:
        for method in typ.get("methods", []):
            all_sigs.append(method.get("signature", ""))
    all_types = [
        t.get("type", "")
        for t in sum([typ.get("properties", []) for typ in content.types], [])
    ]
    combined = " ".join(all_sigs + all_types)

    if "Any" in combined:
        imports.add("from typing import Any")

    # Check for known stdlib types
    for pattern, import_stmt in STDLIB_TYPE_IMPORTS.items():
        if re.search(pattern, combined):
            imports.add(import_stmt)

    if type_module_map:
        referenced_types = set()

        for func in content.functions:
            sig = func.get("signature", "")
            for word in re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", sig):
                if word in type_module_map:
                    referenced_types.add(word)

        for typ in content.types:
            for prop in typ.get("properties", []):
                prop_type = prop.get("type", "")
                for word in re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", prop_type):
                    if word in type_module_map:
                        referenced_types.add(word)

        module_imports: dict[str, list[str]] = defaultdict(list)
        for type_name in referenced_types:
            type_module = type_module_map[type_name]
            if type_module != current_module:
                module_imports[type_module].append(type_name)

        for mod, type_names in sorted(module_imports.items()):
            names = ", ".join(sorted(type_names))
            imports.add(f"from {mod} import {names}")

    # Collect base class imports (multi-stage resolution)
    for typ in content.types:
        for base in typ.get("bases", []):
            # Stage 1: Check KNOWN_BASE_IMPORTS
            if base in KNOWN_BASE_IMPORTS:
                import_stmt = KNOWN_BASE_IMPORTS[base]
                if import_stmt:  # None means builtin, no import needed
                    imports.add(import_stmt)
                continue

            # Stage 2: Check type_module_map (base defined elsewhere in spec)
            if type_module_map and base in type_module_map:
                base_module = type_module_map[base]
                if base_module != current_module:
                    imports.add(f"from {base_module} import {base}")
                continue

            # Stage 3: Check if base matches a stdlib pattern (e.g., Pattern, Iterator)
            found_stdlib = False
            for pattern, import_stmt in STDLIB_TYPE_IMPORTS.items():
                if re.match(pattern.replace(r"\b", "^") + "$", base):
                    imports.add(import_stmt)
                    found_stdlib = True
                    break
            if found_stdlib:
                continue

            # Stage 4: Infer from naming conventions
            # e.g., EventBase -> events module, LayoutMixin -> layout module
            if base.endswith("Base") or base.endswith("Mixin"):
                # Extract the prefix and try to find a matching module
                prefix = base[:-4] if base.endswith("Base") else base[:-5]
                prefix_lower = prefix.lower()
                # Check if any module path ends with this prefix
                if type_module_map:
                    for mod_path in set(type_module_map.values()):
                        mod_name = mod_path.rsplit(".", 1)[-1]
                        if mod_name == prefix_lower or mod_name.startswith(prefix_lower):
                            imports.add(f"from {mod_path} import {base}")
                            break

            # Stage 5: Unresolved base - will need manual import (no warning here, just skip)

    # Collect decorator imports
    for func in content.functions:
        for dec in func.get("decorators", []):
            if isinstance(dec, str):
                # Simple string decorator
                if dec in STDLIB_DECORATOR_IMPORTS:
                    module = STDLIB_DECORATOR_IMPORTS[dec]
                    imports.add(f"from {module} import {dec}")
            else:
                # DecoratorSpec dict
                name = dec.get("name", "")
                import_from = dec.get("import_from")
                root = name.split(".")[0]

                if import_from:
                    # Explicit import_from: from {import_from} import {root}
                    imports.add(f"from {import_from} import {root}")
                elif "." in name:
                    # Dotted name without import_from: import {root}
                    imports.add(f"import {root}")
                elif name in STDLIB_DECORATOR_IMPORTS:
                    # Known stdlib decorator
                    module = STDLIB_DECORATOR_IMPORTS[name]
                    imports.add(f"from {module} import {name}")
                # else: assume it's builtin or already imported

    return sorted(imports)


def collect_generic_params(content: ModuleContent) -> list[dict]:
    """Collect all unique generic parameters from types and functions in a module.

    Returns a list of unique GenericParam dicts, preserving first occurrence order.
    """
    seen_names: set[str] = set()
    params: list[dict] = []

    # Collect from types
    for typ in content.types:
        for param in typ.get("generic_params", []):
            name = param.get("name")
            if name and name not in seen_names:
                seen_names.add(name)
                params.append(param)

    # Collect from functions
    for func in content.functions:
        for param in func.get("generic_params", []):
            name = param.get("name")
            if name and name not in seen_names:
                seen_names.add(name)
                params.append(param)

    return params


def generate_type_var_ast(param: dict) -> ast.Assign:
    """Generate AST for a type variable definition (TypeVar, ParamSpec, TypeVarTuple)."""
    name = param["name"]
    kind = param.get("kind", "type_var")

    # Determine the constructor name based on kind
    if kind == "param_spec":
        constructor = "ParamSpec"
    elif kind == "type_var_tuple":
        constructor = "TypeVarTuple"
    else:
        constructor = "TypeVar"

    # Build the call arguments
    args: list[ast.expr] = [ast.Constant(value=name)]
    keywords: list[ast.keyword] = []

    if kind == "type_var":
        # Handle TypeVar-specific arguments
        bound = param.get("bound")
        constraints = param.get("constraints", [])
        variance = param.get("variance", "invariant")
        default = param.get("default")

        # Add constraints as positional arguments (TypeVar("T", int, str))
        for constraint in constraints:
            args.append(ast.Name(id=constraint, ctx=ast.Load()))

        # Add bound as keyword argument
        if bound:
            keywords.append(
                ast.keyword(arg="bound", value=ast.Name(id=bound, ctx=ast.Load()))
            )

        # Add variance
        if variance == "covariant":
            keywords.append(
                ast.keyword(arg="covariant", value=ast.Constant(value=True))
            )
        elif variance == "contravariant":
            keywords.append(
                ast.keyword(arg="contravariant", value=ast.Constant(value=True))
            )

        # Add default (Python 3.13+)
        if default:
            keywords.append(
                ast.keyword(arg="default", value=ast.Name(id=default, ctx=ast.Load()))
            )

    elif kind in ("param_spec", "type_var_tuple"):
        # ParamSpec and TypeVarTuple only support default (Python 3.13+)
        default = param.get("default")
        if default:
            keywords.append(
                ast.keyword(arg="default", value=ast.Name(id=default, ctx=ast.Load()))
            )

    # Create the assignment: T = TypeVar("T", ...)
    return ast.Assign(
        targets=[ast.Name(id=name, ctx=ast.Store())],
        value=ast.Call(
            func=ast.Name(id=constructor, ctx=ast.Load()),
            args=args,
            keywords=keywords,
        ),
    )


def generate_module_header(module_path: str, spec: dict | None = None) -> str:
    """Generate module header docstring with description."""
    lines = [f"Generated stubs for {module_path}."]

    if spec:
        library = spec.get("library", {})

        for mod in library.get("modules", []):
            if mod.get("path") == module_path:
                desc = mod.get("description")
                if desc:
                    lines.append("")
                    lines.append(desc)
                break

    lines.append("")
    lines.append("Generated by libspec codegen from libspec.json.")

    return '"""' + "\n".join(lines) + '\n"""'


def generate_module_code(
    module_path: str,
    content: ModuleContent,
    type_module_map: dict[str, str] | None = None,
    use_pydantic: bool = False,
    spec: dict | None = None,
) -> str:
    """Generate complete Python code for a module."""
    body: list[ast.stmt] = []

    mod_docstring = generate_module_header(module_path, spec)
    body.append(ast.Expr(value=ast.Constant(value=mod_docstring)))

    imports = collect_imports(content, type_module_map, module_path, use_pydantic)
    for imp in imports:
        try:
            imp_ast = ast.parse(imp).body[0]
            body.append(imp_ast)
        except SyntaxError:
            pass

    body.append(ast.Pass())

    # Generate type variable definitions after imports
    generic_params = collect_generic_params(content)
    for param in generic_params:
        body.append(generate_type_var_ast(param))

    for typ in content.types:
        body.append(generate_type_ast(typ, use_pydantic))

    # Collect function notes for post-processing
    function_notes: dict[str, str] = {}
    for func in content.functions:
        body.append(generate_function_ast(func, spec=spec))
        if func.get("notes"):
            function_notes[func["name"]] = func["notes"]

    module = ast.Module(body=body, type_ignores=[])
    ast.fix_missing_locations(module)

    code = ast.unparse(module)

    code = _fix_module_docstring(code)
    code = _insert_function_notes(code, function_notes)

    lines = code.split("\n")
    cleaned = []
    for line in lines:
        if line.strip() == "pass" and len(cleaned) > 0:
            if (
                cleaned[-1].strip().endswith('"""')
                or cleaned[-1].strip().startswith("from ")
                or cleaned[-1].strip().startswith("import ")
            ):
                cleaned.append("")
                continue
        cleaned.append(line)

    return "\n".join(cleaned)


def _fix_module_docstring(code: str) -> str:
    """Fix module docstring that gets double-quoted by ast.unparse."""
    lines = code.split("\n")
    if not lines:
        return code

    first_line = lines[0]
    if first_line.startswith("'") or first_line.startswith('"'):
        if first_line.startswith("'\"\"\"") or first_line.startswith('\'"""'):
            lines[0] = first_line[1:]
            for i, line in enumerate(lines):
                if line.rstrip().endswith("\"\"\"'"):
                    lines[i] = line.rstrip()[:-1]
                    break
        elif first_line.startswith("'''\"\"\""):
            lines[0] = first_line[3:]
            for i, line in enumerate(lines):
                if line.rstrip().endswith("\"\"\"'''"):
                    lines[i] = line.rstrip()[:-3]
                    break

    return "\n".join(lines)


def _insert_function_notes(code: str, function_notes: dict[str, str]) -> str:
    """Insert implementation notes as comments before raise NotImplementedError."""
    if not function_notes:
        return code

    lines = code.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Look for: raise NotImplementedError("func_name not implemented")
        # ast.unparse may use single or double quotes
        stripped = line.strip()
        if stripped.startswith("raise NotImplementedError("):
            # Extract function name from the error message
            for func_name, notes in function_notes.items():
                # Check both quote styles
                if (
                    f'"{func_name} not implemented"' in stripped
                    or f"'{func_name} not implemented'" in stripped
                ):
                    # Get indentation from current line
                    indent = line[: len(line) - len(line.lstrip())]

                    # Format notes as comments
                    result.append(f"{indent}# Implementation notes:")
                    for note_line in notes.split("\n"):
                        if note_line.strip():
                            result.append(f"{indent}# {note_line}")
                        else:
                            result.append(f"{indent}#")
                    break

        result.append(line)
        i += 1

    return "\n".join(result)


def build_import_graph(
    modules: dict[str, ModuleContent],
    type_module_map: dict[str, str],
) -> dict[str, set[str]]:
    """Build a graph of module import dependencies.

    Returns a dict mapping module paths to the set of modules they import from.
    """
    graph: dict[str, set[str]] = {mod: set() for mod in modules}

    for module_path, content in modules.items():
        imported_modules: set[str] = set()

        # Check type references in signatures and properties
        for func in content.functions:
            sig = func.get("signature", "")
            for word in re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", sig):
                if word in type_module_map:
                    imported_modules.add(type_module_map[word])

        for typ in content.types:
            # Check property types
            for prop in typ.get("properties", []):
                prop_type = prop.get("type", "")
                for word in re.findall(r"\b([A-Z][a-zA-Z0-9]*)\b", prop_type):
                    if word in type_module_map:
                        imported_modules.add(type_module_map[word])

            # Check base classes
            for base in typ.get("bases", []):
                if base in type_module_map:
                    imported_modules.add(type_module_map[base])

        # Remove self-imports and add to graph
        imported_modules.discard(module_path)
        graph[module_path] = imported_modules

    return graph


def find_import_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Find all cycles in the import dependency graph using DFS.

    Returns a list of cycles, where each cycle is a list of module paths.
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def dfs(node: str, path: list[str]) -> None:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor, path)
            elif neighbor in rec_stack:
                # Found a cycle - extract it
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                # Normalize cycle to avoid duplicates (start with smallest element)
                min_idx = cycle.index(min(cycle[:-1]))
                normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                if normalized not in cycles:
                    cycles.append(normalized)

        path.pop()
        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            dfs(node, [])

    return cycles


def format_with_ruff(code: str) -> str:
    """Format code using ruff."""
    try:
        result = subprocess.run(
            ["ruff", "format", "--stdin-filename", "generated.py"],
            input=code,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return code


def generate_init_code(
    module_path: str,
    exports: list[str],
    type_module_map: dict[str, str],
    spec: dict,
    warnings: list[str] | None = None,
) -> str:
    """Generate __init__.py content for a package.

    Args:
        module_path: The module path (e.g., "mylib.models")
        exports: List of names to export
        type_module_map: Map of type names to their module paths
        spec: The full libspec
        warnings: Optional list to collect warnings about invalid exports
    """
    if not exports:
        return ""

    submodule_imports: dict[str, list[str]] = {}
    library = spec.get("library", {})

    # Build set of all valid function names for validation
    valid_functions = {func["name"] for func in library.get("functions", [])}

    for name in exports:
        if name in type_module_map:
            full_module = type_module_map[name]
        else:
            for func in library.get("functions", []):
                if func["name"] == name:
                    full_module = func.get("module", module_path)
                    break
            else:
                # Export not found in types or functions - emit warning
                if warnings is not None:
                    if name not in valid_functions and name not in type_module_map:
                        warnings.append(
                            f"Export '{name}' in module '{module_path}' not found "
                            "in spec types or functions"
                        )
                continue

        if full_module.startswith(module_path + "."):
            submodule = full_module[len(module_path) + 1 :]
            if "." in submodule:
                submodule = submodule.split(".")[0]
        else:
            continue

        if submodule not in submodule_imports:
            submodule_imports[submodule] = []
        submodule_imports[submodule].append(name)

    if not submodule_imports:
        return ""

    module_desc = None
    for mod in library.get("modules", []):
        if mod.get("path") == module_path:
            module_desc = mod.get("description")
            break

    docstring = module_desc if module_desc else f"Exports for {module_path}."
    lines = [f'"""{docstring}"""', "", "from __future__ import annotations", ""]

    for submodule in sorted(submodule_imports.keys()):
        names = sorted(submodule_imports[submodule])
        if len(names) == 1:
            lines.append(f"from .{submodule} import {names[0]}")
        else:
            lines.append(f"from .{submodule} import (")
            for name in names:
                lines.append(f"    {name},")
            lines.append(")")

    lines.append("")
    lines.append(f"__all__ = {sorted(exports)!r}")
    lines.append("")

    return "\n".join(lines)


# === CLI Commands ===


@click.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output directory for generated files",
)
@click.option(
    "--module",
    "-m",
    "module_name",
    help="Generate only this module (prints to stdout)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print generated code instead of writing files",
)
@click.option(
    "--no-format",
    is_flag=True,
    help="Skip ruff formatting",
)
@click.option(
    "--pydantic",
    is_flag=True,
    help="Generate Pydantic models instead of dataclasses",
)
@click.option(
    "--list-modules",
    is_flag=True,
    help="List available modules and exit",
)
@click.option(
    "--skip-implemented",
    is_flag=True,
    help="Skip entities with maturity='implemented' or 'tested'",
)
@pass_context
def codegen(
    ctx: Context,
    output: str | None,
    module_name: str | None,
    dry_run: bool,
    no_format: bool,
    pydantic: bool,
    list_modules: bool,
    skip_implemented: bool,
) -> None:
    """
    Generate Python stubs from libspec.json.

    \b
    Generates:
    - Function stubs with signatures, type hints, and docstrings
    - Type definitions (dataclasses, enums, classes)
    - __init__.py files with exports

    \b
    Examples:
        libspec codegen --list-modules           # Show available modules
        libspec codegen -o src/                  # Generate all to src/
        libspec codegen -m mylib.server          # One module to stdout
        libspec codegen --pydantic -o generated/ # Use Pydantic models
        libspec codegen --dry-run                # Preview all files to stdout
    """
    loaded = ctx.get_spec()
    spec = loaded.data  # Get raw dict data for codegen

    library = spec.get("library", {})
    format_code = not no_format
    skip_maturity = {"implemented", "tested"} if skip_implemented else None

    type_module_map = build_type_module_map(spec)
    modules = group_by_module(spec, skip_maturity)

    # List modules mode
    if list_modules:
        module_list = sorted(modules.keys())
        if ctx.text:
            for mod in module_list:
                click.echo(mod)
        else:
            click.echo(f"Modules in spec ({len(module_list)}):")
            for mod in module_list:
                click.echo(f"  {mod}")
        return

    # Single module mode
    if module_name:
        if module_name not in modules:
            raise click.ClickException(f"Module '{module_name}' not found in spec")

        code = generate_module_code(
            module_name,
            modules[module_name],
            type_module_map=type_module_map,
            use_pydantic=pydantic,
            spec=spec,
        )
        if format_code:
            code = format_with_ruff(code)
        click.echo(code)
        return

    # Generate all mode (triggered by -o or --dry-run)
    if output or dry_run:
        output_dir = Path(output) if output else Path(".")
        results: list[GenerationResult] = []

        for module_path, content in modules.items():
            code = generate_module_code(
                module_path,
                content,
                type_module_map=type_module_map,
                use_pydantic=pydantic,
                spec=spec,
            )
            if format_code:
                code = format_with_ruff(code)

            parts = module_path.split(".")
            file_path = output_dir / "/".join(parts[:-1]) / f"{parts[-1]}.py"

            result = GenerationResult(
                module=module_path,
                code=code,
                path=file_path,
            )

            if not dry_run:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code)

            results.append(result)

        # Generate __init__.py files
        spec_modules = library.get("modules", [])
        export_warnings: list[str] = []
        for mod_info in spec_modules:
            exports = mod_info.get("exports", [])
            mod_path = mod_info.get("path", "")

            if exports:
                init_code = generate_init_code(
                    mod_path, exports, type_module_map, spec, export_warnings
                )
                if not init_code:
                    continue
            else:
                desc = mod_info.get("description", "")
                lib_name = library.get("name", "")

                if mod_path == lib_name:
                    version = library.get("version", "")
                    tagline = library.get("tagline", desc)
                    lib_desc = library.get("description", "")
                    lines = [f'"""{tagline}']
                    if lib_desc and lib_desc != tagline:
                        lines.append("")
                        lines.append(lib_desc)
                    if version:
                        lines.append("")
                        lines.append(f"Version: {version}")
                    lines.append('"""')
                    if version:
                        lines.append("")
                        lines.append(f'__version__ = "{version}"')
                    init_code = "\n".join(lines) + "\n"
                elif desc:
                    init_code = f'"""{desc}"""\n'
                else:
                    init_code = f'"""Package {mod_path}."""\n'

            if format_code:
                init_code = format_with_ruff(init_code)

            parts = mod_path.split(".")
            init_file_path = output_dir / "/".join(parts) / "__init__.py"

            result = GenerationResult(
                module=f"{mod_path}.__init__",
                code=init_code,
                path=init_file_path,
            )

            if not dry_run:
                init_file_path.parent.mkdir(parents=True, exist_ok=True)
                init_file_path.write_text(init_code)

            results.append(result)

        # Check for circular imports
        import_graph = build_import_graph(modules, type_module_map)
        import_cycles = find_import_cycles(import_graph)

        # Output warnings
        all_warnings: list[str] = []
        all_warnings.extend(export_warnings)
        for cycle in import_cycles:
            cycle_path = " → ".join(cycle)
            all_warnings.append(f"Potential circular import: {cycle_path}")

        if all_warnings:
            click.secho("\nWarnings:", fg="yellow")
            for warning in all_warnings:
                click.secho(f"  • {warning}", fg="yellow")

        # Output results
        if dry_run:
            total_lines = 0
            for result in results:
                line_count = result.code.count('\n') + 1
                total_lines += line_count
                click.echo(f"# --- {result.path} ({line_count} lines) ---")
                click.echo(result.code)
                click.echo()
            click.echo(f"# Would generate {len(results)} files ({total_lines} lines)")
        else:
            for result in results:
                click.echo(f"Generated: {result.path}")
            click.echo(f"\n{len(results)} files generated")
        return

    # Default: list modules
    module_list = sorted(modules.keys())
    click.echo(f"Modules in spec ({len(module_list)}):")
    for mod in module_list:
        click.echo(f"  {mod}")
    click.echo()
    click.echo("Use --output to generate files, --module to generate one module")
