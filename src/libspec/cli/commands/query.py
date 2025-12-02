"""Query commands: query, refs, search."""

import re
from typing import Any

import click

from libspec.cli.app import Context, pass_context
from libspec.cli.jq import JqError, JqNotFoundError, resolve_shortcut, run_jq
from libspec.cli.output import make_envelope, output_json


def parse_ref(ref: str) -> list[str]:
    """
    Parse a cross-reference into path components.

    Examples:
        #/types/Handle -> ['types', 'Handle']
        #/types/Handle/methods/send -> ['types', 'Handle', 'methods', 'send']
        #/functions/spawn -> ['functions', 'spawn']
    """
    if ref.startswith("#/"):
        ref = ref[2:]
    return ref.split("/")


def resolve_ref(spec_data: dict[str, Any], ref: str) -> tuple[Any, list[str | int]] | None:
    """
    Resolve a cross-reference to its value and path.

    Returns:
        Tuple of (resolved_value, json_path) or None if not found
    """
    parts = parse_ref(ref)
    if not parts:
        return None

    library = spec_data.get("library", {})
    json_path: list[str | int] = ["library"]

    # First part is the collection type
    collection = parts[0]
    if collection not in ("types", "functions", "features", "modules", "principles"):
        return None

    items = library.get(collection, [])
    json_path.append(collection)

    if len(parts) < 2:
        return items, json_path

    # Second part is the item name/id
    name = parts[1]
    name_key = "id" if collection in ("features", "principles") else "name"

    for i, item in enumerate(items):
        if item.get(name_key) == name:
            json_path.append(i)

            # If more parts, traverse deeper
            if len(parts) > 2:
                current = item
                for part in parts[2:]:
                    if isinstance(current, dict):
                        if part in current:
                            current = current[part]
                            json_path.append(part)
                        else:
                            # Try as array lookup by name
                            arr = current.get(part, [])
                            if isinstance(arr, list) and len(parts) > parts.index(part) + 1:
                                next_name = parts[parts.index(part) + 1]
                                for j, elem in enumerate(arr):
                                    if elem.get("name") == next_name:
                                        current = elem
                                        json_path.extend([part, j])
                                        break
                                else:
                                    return None
                            else:
                                return None
                    else:
                        return None
                return current, json_path
            return item, json_path

    return None


@click.command()
@click.argument("expression")
@click.option("--raw", "-r", is_flag=True, help="Output raw strings without JSON encoding (-r)")
@click.option("--compact", "-c", is_flag=True, help="Compact single-line output (-c)")
@pass_context
def query(ctx: Context, expression: str, raw: bool, compact: bool) -> None:
    """
    Run a jq expression against the spec.

    \b
    EXPRESSION is passed directly to jq. The full spec is provided as input.
    Requires jq to be installed (https://jqlang.github.io/jq/).

    \b
    Shortcuts (expand to jq expressions):
        type-names      → .library.types[].name
        function-names  → .library.functions[].name
        feature-ids     → .library.features[].id
        modules         → .library.modules[].path
        extensions      → .extensions

    \b
    Examples:
        libspec query '.library.types[].name'
        libspec query '.library.types[] | select(.kind=="protocol")'
        libspec query type-names -r
        libspec query '.library.features | length'
    """
    spec = ctx.get_spec()
    expr = resolve_shortcut(expression)

    try:
        result = run_jq(spec.data, expr, raw=raw, compact=compact)
        # jq output goes directly to stdout
        click.echo(result, nl=False)
    except JqNotFoundError as e:
        raise click.ClickException(str(e))
    except JqError as e:
        raise click.ClickException(str(e))


@click.command()
@click.argument("reference")
@pass_context
def refs(ctx: Context, reference: str) -> None:
    """
    Resolve a cross-reference to its full definition.

    \b
    REFERENCE uses JSON Pointer syntax:
        #/types/Handle              → Type definition
        #/types/Handle/methods/send → Specific method
        #/functions/spawn           → Function definition
        #/features/connection-retry → Feature by ID

    \b
    Examples:
        libspec refs '#/types/Connection'
        libspec refs '#/types/Connection/methods/send'
    """
    spec = ctx.get_spec()
    result = resolve_ref(spec.data, reference)

    if result is None:
        raise click.ClickException(f"Reference not found: {reference}")

    resolved, path = result

    if ctx.text:
        if isinstance(resolved, dict):
            name = resolved.get("name") or resolved.get("id") or "?"
            click.echo(f"REF {reference} -> {name}")
            if "signature" in resolved:
                click.echo(f"  {resolved['signature']}")
            if "description" in resolved or "docstring" in resolved:
                desc = resolved.get("description") or resolved.get("docstring") or ""
                click.echo(f"  {desc[:80]}")
        else:
            click.echo(f"REF {reference} -> {resolved}")
        return

    envelope = make_envelope(
        "refs",
        spec,
        {
            "ref": reference,
            "resolved": resolved,
            "path": path,
        },
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.argument("pattern")
@click.option(
    "--in",
    "search_in",
    type=click.Choice(["names", "descriptions", "all"]),
    default="all",
    help="Where to search (default: all)",
)
@click.option(
    "--type",
    "entity_type",
    type=click.Choice(["types", "functions", "features", "all"]),
    default="all",
    help="Entity types to search (default: all)",
)
@pass_context
def search(ctx: Context, pattern: str, search_in: str, entity_type: str) -> None:
    """
    Search for PATTERN across the spec.

    \b
    PATTERN is a regex matched case-insensitively.
    Returns matching entities with context around the match.

    \b
    Examples:
        libspec search connection
        libspec search 'async.*handler' --type types
        libspec search retry --in descriptions
    """
    spec = ctx.get_spec()
    results: list[dict[str, Any]] = []

    try:
        regex = re.compile(pattern, re.IGNORECASE)
    except re.error as e:
        raise click.ClickException(f"Invalid regex pattern: {e}")

    def check_match(text: str | None) -> str | None:
        if text and regex.search(text):
            # Extract context around match
            match = regex.search(text)
            if match:
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                return f"...{text[start:end]}..."
        return None

    # Search types
    if entity_type in ("types", "all"):
        for t in spec.types:
            name = t.name
            docstring = t.docstring or ""

            match_in = None
            context = None

            if search_in in ("names", "all"):
                ctx_match = check_match(name)
                if ctx_match:
                    match_in = "name"
                    context = name

            if not match_in and search_in in ("descriptions", "all"):
                ctx_match = check_match(docstring)
                if ctx_match:
                    match_in = "docstring"
                    context = ctx_match

            if match_in:
                results.append(
                    {
                        "entity": "type",
                        "name": name,
                        "match_in": match_in,
                        "context": context,
                        "ref": f"#/types/{name}",
                    }
                )

    # Search functions
    if entity_type in ("functions", "all"):
        for f in spec.functions:
            name = f.name
            desc = f.description or ""

            match_in = None
            context = None

            if search_in in ("names", "all") and check_match(name):
                match_in = "name"
                context = name

            if not match_in and search_in in ("descriptions", "all"):
                ctx_match = check_match(desc)
                if ctx_match:
                    match_in = "description"
                    context = ctx_match

            if match_in:
                results.append(
                    {
                        "entity": "function",
                        "name": name,
                        "match_in": match_in,
                        "context": context,
                        "ref": f"#/functions/{name}",
                    }
                )

    # Search features
    if entity_type in ("features", "all"):
        for feat in spec.features:
            fid = feat.id
            summary = feat.summary or ""
            desc = feat.description or ""

            match_in = None
            context = None

            if search_in in ("names", "all") and check_match(fid):
                match_in = "id"
                context = fid

            if not match_in and search_in in ("descriptions", "all"):
                for field, val in [("summary", summary), ("description", desc)]:
                    ctx_match = check_match(val)
                    if ctx_match:
                        match_in = field
                        context = ctx_match
                        break

            if match_in:
                results.append(
                    {
                        "entity": "feature",
                        "name": fid,
                        "match_in": match_in,
                        "context": context,
                        "ref": f"#/features/{fid}",
                    }
                )

    if ctx.text:
        for r in results:
            click.echo(f"MATCH {r['entity']} {r['name']} in:{r['match_in']}")
        click.echo("---")
        click.echo(f"{len(results)} matches")
        return

    envelope = make_envelope(
        "search",
        spec,
        results,
        meta={"count": len(results), "pattern": pattern},
    )
    output_json(envelope, ctx.no_meta)
