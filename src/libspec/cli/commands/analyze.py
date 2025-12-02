"""Analyze commands: coverage, deps, surface."""

import re
from collections import defaultdict
from typing import Any

import click

from libspec.cli.app import Context, pass_context
from libspec.cli.output import make_envelope, output_json
from libspec.models import TypeDef


def extract_refs_from_type(type_def: TypeDef) -> set[str]:
    """Extract type references from a type definition."""
    refs = set()

    # Bases
    for base in type_def.bases:
        if not base.startswith(("#", "typing.", "collections.")):
            refs.add(base)

    # Related
    for ref in type_def.related:
        if ref.startswith("#/types/"):
            refs.add(ref.split("/")[-1])

    # Properties types
    for prop in type_def.properties:
        ptype = prop.type or ""
        # Extract type names from type annotations
        for match in re.findall(r"[A-Z][a-zA-Z0-9]*", ptype):
            refs.add(match)

    # Method signatures
    for method in type_def.methods:
        sig = method.signature
        for match in re.findall(r"[A-Z][a-zA-Z0-9]*", sig):
            refs.add(match)

    return refs


@click.command()
@click.option(
    "--type",
    "coverage_type",
    type=click.Choice(["features", "docs", "all"]),
    default="all",
    help="Type of coverage to analyze (default: all)",
)
@click.option("--threshold", type=float, help="Minimum coverage % to pass (not yet implemented)")
@pass_context
def coverage(ctx: Context, coverage_type: str, threshold: float | None) -> None:
    """
    Analyze feature and documentation coverage.

    \b
    Reports:
      - Feature status: planned → implemented → tested
      - Documentation: types and methods with descriptions

    \b
    Also lists gaps (undocumented types, untested features).

    \b
    Examples:
        libspec coverage
        libspec coverage --type features
        libspec coverage | jq '.result.gaps[]'
    """
    spec = ctx.get_spec()

    result: dict[str, Any] = {}
    gaps: list[dict[str, Any]] = []

    if coverage_type in ("features", "all"):
        features = spec.features
        total = len(features)
        planned = sum(1 for f in features if f.status == "planned")
        implemented = sum(1 for f in features if f.status == "implemented")
        tested = sum(1 for f in features if f.status == "tested")

        result["features"] = {
            "total": total,
            "planned": planned,
            "implemented": implemented,
            "tested": tested,
            "coverage_pct": round((implemented + tested) / total * 100, 1) if total else 0,
        }

        # Find gaps
        for f in features:
            if f.status == "planned":
                gaps.append({
                    "entity": "feature",
                    "id": f.id,
                    "issue": "not implemented",
                })
            elif f.status == "implemented":
                gaps.append({
                    "entity": "feature",
                    "id": f.id,
                    "issue": "not tested",
                })

    if coverage_type in ("docs", "all"):
        types = spec.types
        types_total = len(types)
        types_documented = sum(1 for t in types if t.docstring)

        methods_total = 0
        methods_documented = 0
        for t in types:
            for m in t.methods:
                methods_total += 1
                if m.description:
                    methods_documented += 1

        result["documentation"] = {
            "types_documented": types_documented,
            "types_total": types_total,
            "methods_documented": methods_documented,
            "methods_total": methods_total,
            "coverage_pct": round(
                (types_documented + methods_documented)
                / (types_total + methods_total)
                * 100,
                1,
            )
            if (types_total + methods_total)
            else 0,
        }

        # Find gaps
        for t in types:
            if not t.docstring:
                gaps.append({
                    "entity": "type",
                    "name": t.name,
                    "issue": "no docstring",
                })

    result["gaps"] = gaps

    if ctx.text:
        if "features" in result:
            f = result["features"]
            click.echo(
                f"features: {f['implemented']+f['tested']}/{f['total']} "
                f"({f['coverage_pct']}%)"
            )
        if "documentation" in result:
            d = result["documentation"]
            click.echo(
                f"docs: {d['types_documented']+d['methods_documented']}/"
                f"{d['types_total']+d['methods_total']} ({d['coverage_pct']}%)"
            )
        click.echo(f"---\n{len(gaps)} gaps")
        return

    envelope = make_envelope(
        "coverage",
        spec,
        result,
        meta={"gap_count": len(gaps)},
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option("--type", "type_name", help="Analyze deps for a specific type")
@click.option("--module", help="Analyze deps for a specific module")
@click.option("--reverse", is_flag=True, help="Show what depends ON this entity")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "dot", "mermaid"]),
    default="json",
    help="Output format (default: json)",
)
@pass_context
def deps(
    ctx: Context,
    type_name: str | None,
    module: str | None,
    reverse: bool,
    output_format: str,
) -> None:
    """
    Analyze type and module dependencies.

    \b
    Builds a dependency graph from type references (bases, signatures,
    properties) and module depends_on declarations.

    \b
    Examples:
        libspec deps                        # Full graph
        libspec deps --type Connection      # What Connection uses
        libspec deps --type Connection --reverse  # What uses Connection
        libspec deps --format dot | dot -Tpng > deps.png
        libspec deps --format mermaid
    """
    spec = ctx.get_spec()

    # Build type dependency graph
    type_deps: dict[str, set[str]] = defaultdict(set)
    type_names = {t.name for t in spec.types}

    for t in spec.types:
        name = t.name
        refs = extract_refs_from_type(t)
        # Filter to only types that exist in this spec
        type_deps[name] = refs & type_names

    # Build module dependency graph
    module_deps: dict[str, list[str]] = {}
    for m in spec.modules:
        path = m.path
        module_deps[path] = m.depends_on

    # If specific type requested
    if type_name:
        if type_name not in type_deps:
            raise click.ClickException(f"Type '{type_name}' not found")

        if reverse:
            # Find what depends on this type
            dependents = [n for n, d in type_deps.items() if type_name in d]
            result: dict[str, Any] = {"type": type_name, "depended_by": dependents}
        else:
            result = {"type": type_name, "depends_on": list(type_deps[type_name])}
    elif module:
        if module not in module_deps:
            raise click.ClickException(f"Module '{module}' not found")

        if reverse:
            dependents = [m_path for m_path, d in module_deps.items() if module in d]
            result = {"module": module, "depended_by": dependents}
        else:
            result = {"module": module, "depends_on": module_deps[module]}
    else:
        # Full graph
        result = {
            "types": {k: list(v) for k, v in type_deps.items() if v},
            "modules": module_deps,
        }

    # Handle different output formats
    if output_format == "dot":
        lines = ["digraph deps {"]
        for name, deps_set in type_deps.items():
            for dep in deps_set:
                lines.append(f'  "{name}" -> "{dep}";')
        lines.append("}")
        click.echo("\n".join(lines))
        return

    if output_format == "mermaid":
        lines = ["graph TD"]
        for name, deps_set in type_deps.items():
            for dep in deps_set:
                lines.append(f"  {name} --> {dep}")
        click.echo("\n".join(lines))
        return

    if ctx.text:
        if type_name or module:
            entity = type_name or module
            deps_list = result.get("depends_on") or result.get("depended_by", [])
            direction = "depended_by" if reverse else "depends_on"
            click.echo(f"{entity} {direction}: {', '.join(deps_list) or 'none'}")
        else:
            for name, deps_set in type_deps.items():
                if deps_set:
                    click.echo(f"TYPE {name} -> {', '.join(deps_set)}")
            click.echo("---")
            click.echo(f"{len([d for d in type_deps.values() if d])} types with deps")
        return

    envelope = make_envelope("deps", spec, result)
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option("--public-only", is_flag=True, help="Exclude internal modules")
@click.option("--by-module", is_flag=True, help="Break down counts by module")
@pass_context
def surface(ctx: Context, public_only: bool, by_module: bool) -> None:
    """
    Analyze public API surface area.

    \b
    Counts types, functions, methods, and properties to measure
    the size of the public interface.

    \b
    Examples:
        libspec surface
        libspec surface --by-module
        libspec surface --public-only
    """
    spec = ctx.get_spec()

    # Get internal modules
    internal_modules = {m.path for m in spec.modules if m.internal}

    # Count entities
    types_count = 0
    functions_count = 0
    methods_count = 0
    properties_count = 0

    by_mod: dict[str, dict[str, int]] = defaultdict(lambda: {
        "types": 0, "functions": 0, "methods": 0, "properties": 0
    })

    for t in spec.types:
        mod = t.module
        if public_only and mod in internal_modules:
            continue

        types_count += 1
        by_mod[mod]["types"] += 1

        methods = len(t.methods)
        properties = len(t.properties)
        methods_count += methods
        properties_count += properties
        by_mod[mod]["methods"] += methods
        by_mod[mod]["properties"] += properties

    for func in spec.functions:
        mod = func.module
        if public_only and mod in internal_modules:
            continue

        functions_count += 1
        by_mod[mod]["functions"] += 1

    result: dict[str, Any] = {
        "public_types": types_count,
        "public_functions": functions_count,
        "total_methods": methods_count,
        "total_properties": properties_count,
    }

    if by_module:
        result["by_module"] = dict(by_mod)

    if ctx.text:
        click.echo(f"types: {types_count}")
        click.echo(f"functions: {functions_count}")
        click.echo(f"methods: {methods_count}")
        click.echo(f"properties: {properties_count}")
        total = types_count + functions_count + methods_count + properties_count
        click.echo(f"---\n{total} total surface")
        return

    envelope = make_envelope(
        "surface",
        spec,
        result,
        meta={
            "total_surface": types_count + functions_count + methods_count + properties_count
        },
    )
    output_json(envelope, ctx.no_meta)
