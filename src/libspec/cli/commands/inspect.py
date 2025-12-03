"""Inspect commands: info, types, functions, features, modules, principles."""

from __future__ import annotations

import re

import click

from libspec.cli.app import Context, pass_context
from libspec.cli.models.output import (
    CountsResult,
    CoverageResult,
    FeatureSummary,
    FunctionSummary,
    InfoResult,
    LibraryInfo,
    ModuleSummary,
    ModuleTreeNode,
    PrincipleSummary,
    TypeSummary,
)
from libspec.cli.output import (
    build_module_tree,
    make_envelope,
    output_json,
    output_text_features,
    output_text_functions,
    output_text_info,
    output_text_modules,
    output_text_principles,
    output_text_tree,
    output_text_types,
)
from libspec.cli.spec_loader import LoadedSpec
from libspec.models import Feature, FunctionDef, TypeDef


def compute_counts(spec: LoadedSpec) -> CountsResult:
    """Compute entity counts from a spec."""
    return CountsResult(
        types=len(spec.types),
        functions=len(spec.functions),
        features=len(spec.features),
        modules=len(spec.modules),
        principles=len(spec.principles),
    )


def compute_coverage(spec: LoadedSpec) -> CoverageResult:
    """Compute coverage statistics from a spec."""
    features = spec.features
    types = spec.types

    # Feature coverage
    features_total = len(features)
    features_planned = sum(1 for f in features if f.status == "planned")
    features_implemented = sum(1 for f in features if f.status == "implemented")
    features_tested = sum(1 for f in features if f.status == "tested")

    # Doc coverage
    types_total = len(types)
    types_with_docs = sum(1 for t in types if t.docstring)

    methods_total = 0
    methods_with_docs = 0
    for t in types:
        for m in t.methods:
            methods_total += 1
            if m.description:
                methods_with_docs += 1

    return CoverageResult(
        features_total=features_total,
        features_planned=features_planned,
        features_implemented=features_implemented,
        features_tested=features_tested,
        types_with_docs=types_with_docs,
        types_total=types_total,
        methods_with_docs=methods_with_docs,
        methods_total=methods_total,
    )


@click.command()
@click.option("--counts-only", is_flag=True, help="Only show counts")
@pass_context
def info(ctx: Context, counts_only: bool) -> None:
    """
    Show spec overview: library info, counts, extensions, coverage.

    \b
    This is the recommended starting point for exploring a spec.
    Output includes entity counts, enabled extensions, and
    documentation/feature coverage percentages.

    \b
    Examples:
        libspec info                    # Full overview
        libspec info --counts-only      # Just entity counts
        libspec info -t                 # Token-minimal text
    """
    spec = ctx.get_spec()
    lib = spec.library

    counts = compute_counts(spec)
    coverage = compute_coverage(spec)

    if ctx.text:
        output_text_info(
            spec,
            counts.model_dump(exclude_none=True),
            coverage.model_dump(exclude_none=True),
        )
        return

    if counts_only:
        envelope = make_envelope("info", spec, counts.model_dump(exclude_none=True))
    else:
        result = InfoResult(
            library=LibraryInfo(
                name=lib.name,
                version=lib.version,
                tagline=lib.tagline,
                python_requires=lib.python_requires,
                repository=str(lib.repository) if lib.repository else None,
                documentation=str(lib.documentation) if lib.documentation else None,
            ),
            extensions=spec.extensions,
            counts=counts,
            coverage=coverage,
        )
        envelope = make_envelope("info", spec, result.model_dump(exclude_none=True))

    output_json(envelope, ctx.no_meta)


def _get_lifecycle_state(entity: TypeDef | FunctionDef | Feature) -> str | None:
    """Get lifecycle_state from an entity (extension field)."""
    # Lifecycle state is from the lifecycle extension, accessed via raw data
    # For now, return None as we'd need extension field support
    return getattr(entity, "lifecycle_state", None)


@click.command()
@click.option("--kind", "-k", help="Filter by kind (class, protocol, enum, dataclass, type_alias)")
@click.option("--module", "-m", help="Filter by module path (regex pattern)")
@click.option("--undocumented", is_flag=True, help="Only show types without docstrings")
@click.option("--lifecycle-state", help="Filter by lifecycle_state (requires lifecycle extension)")
@pass_context
def types(
    ctx: Context,
    kind: str | None,
    module: str | None,
    undocumented: bool,
    lifecycle_state: str | None,
) -> None:
    """
    List type definitions (classes, protocols, enums, etc).

    \b
    Each type includes: name, kind, module, method/property counts,
    and a cross-reference for drilling down.

    \b
    Examples:
        libspec types                       # All types
        libspec types --kind protocol       # Only protocols
        libspec types -m 'mylib\\.core'     # Types in mylib.core
        libspec types --undocumented        # Find missing docstrings
        libspec types --lifecycle-state implemented
    """
    spec = ctx.get_spec()
    result: list[TypeSummary] = []

    for t in spec.types:
        # Apply filters
        if kind and t.kind != kind:
            continue
        if module and not re.search(module, t.module):
            continue
        if undocumented and t.docstring:
            continue
        if lifecycle_state and _get_lifecycle_state(t) != lifecycle_state:
            continue

        result.append(
            TypeSummary(
                name=t.name,
                kind=t.kind,
                module=t.module,
                methods_count=len(t.methods),
                properties_count=len(t.properties),
                has_docstring=bool(t.docstring),
                ref=f"#/types/{t.name}",
            )
        )

    if ctx.text:
        output_text_types([r.model_dump(exclude_none=True) for r in result])
        return

    # Compute metadata
    kinds: dict[str, int] = {}
    for r in result:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1

    envelope = make_envelope(
        "types",
        spec,
        [r.model_dump(exclude_none=True) for r in result],
        meta={"count": len(result), "kinds": kinds},
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option(
    "--kind", "-k", help="Filter: function, decorator, context_manager, async_context_manager"
)
@click.option("--module", "-m", help="Filter by module path (regex pattern)")
@click.option("--lifecycle-state", help="Filter by lifecycle_state (requires lifecycle extension)")
@pass_context
def functions(
    ctx: Context,
    kind: str | None,
    module: str | None,
    lifecycle_state: str | None,
) -> None:
    """
    List function definitions.

    \b
    Examples:
        libspec functions                   # All functions
        libspec functions --kind decorator  # Only decorators
        libspec functions --lifecycle-state tested
        libspec functions | jq '.result[].signature'
    """
    spec = ctx.get_spec()
    result: list[FunctionSummary] = []

    for f in spec.functions:
        if kind and f.kind != kind:
            continue
        if module and not re.search(module, f.module):
            continue
        if lifecycle_state and _get_lifecycle_state(f) != lifecycle_state:
            continue

        result.append(
            FunctionSummary(
                name=f.name,
                kind=f.kind,
                module=f.module,
                signature=f.signature,
                has_description=bool(f.description),
                ref=f"#/functions/{f.name}",
            )
        )

    if ctx.text:
        output_text_functions([r.model_dump(exclude_none=True) for r in result])
        return

    kinds: dict[str, int] = {}
    for r in result:
        kinds[r.kind] = kinds.get(r.kind, 0) + 1

    envelope = make_envelope(
        "functions",
        spec,
        [r.model_dump(exclude_none=True) for r in result],
        meta={"count": len(result), "kinds": kinds},
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option(
    "--status",
    "-s",
    type=click.Choice(["planned", "implemented", "tested"]),
    help="Filter by implementation status",
)
@click.option("--category", "-c", help="Filter by category (regex, case-insensitive)")
@click.option("--lifecycle-state", help="Filter by lifecycle_state (requires lifecycle extension)")
@pass_context
def features(
    ctx: Context,
    status: str | None,
    category: str | None,
    lifecycle_state: str | None,
) -> None:
    """
    List feature specifications (behavioral contracts).

    \b
    Features link documentation to testable assertions.
    Use --status to track implementation progress.

    \b
    Examples:
        libspec features                    # All features
        libspec features --status planned   # Not yet implemented
        libspec features -c CONNECTION      # Category filter
        libspec features --lifecycle-state drafted
    """
    spec = ctx.get_spec()
    result: list[FeatureSummary] = []

    for f in spec.features:
        if status and f.status != status:
            continue
        if category and not re.search(category, f.category, re.IGNORECASE):
            continue
        if lifecycle_state and _get_lifecycle_state(f) != lifecycle_state:
            continue

        result.append(
            FeatureSummary(
                id=f.id,
                category=f.category,
                summary=f.summary,
                status=f.status,
                steps_count=len(f.steps),
                refs_count=len(f.references),
                ref=f"#/features/{f.id}",
            )
        )

    if ctx.text:
        output_text_features([r.model_dump(exclude_none=True) for r in result])
        return

    by_status: dict[str, int] = {}
    for r in result:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    envelope = make_envelope(
        "features",
        spec,
        [r.model_dump(exclude_none=True) for r in result],
        meta={"count": len(result), "by_status": by_status},
    )
    output_json(envelope, ctx.no_meta)


@click.command()
@click.option("--tree", is_flag=True, help="Show as hierarchical tree")
@click.option("--internal", is_flag=True, help="Include internal/private modules")
@click.option("--exports", is_flag=True, help="Show exported names (with --tree)")
@click.option("--deps", is_flag=True, help="Show dependencies (with --tree)")
@click.option("--entities", is_flag=True, help="Show types/functions under modules")
@click.option("--depth", type=int, help="Limit tree depth")
@click.option("--types-only", is_flag=True, help="Only show types (with --entities)")
@click.option("--functions-only", is_flag=True, help="Only show functions (with --entities)")
@click.option("--kind", "kind_filter", help="Filter entities by kind (with --entities)")
@click.option("--stats", is_flag=True, help="Show entity counts per module")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "dot", "mermaid"]),
    default=None,
    help="Output format for tree view",
)
@pass_context
def modules(
    ctx: Context,
    tree: bool,
    internal: bool,
    exports: bool,
    deps: bool,
    entities: bool,
    depth: int | None,
    types_only: bool,
    functions_only: bool,
    kind_filter: str | None,
    stats: bool,
    output_format: str | None,
) -> None:
    """
    List module definitions and dependencies.

    \b
    Shows package structure with exports and internal dependencies.

    \b
    Use --tree for hierarchical view:
        libspec modules --tree              # Basic hierarchy
        libspec modules --tree --exports    # Show exported names
        libspec modules --tree --deps       # Show dependencies
        libspec modules --tree --internal   # Include internal modules

    \b
    Use --entities to show types/functions under modules:
        libspec modules --tree --entities   # Show all entities
        libspec modules --tree --entities --types-only
        libspec modules --tree --entities --kind protocol
        libspec modules --tree --depth 2    # Limit depth
        libspec modules --tree --stats      # Show entity counts
    """
    spec = ctx.get_spec()

    # Validate option combinations
    if types_only and functions_only:
        raise click.UsageError("Cannot use both --types-only and --functions-only")
    if (types_only or functions_only or kind_filter) and not entities:
        raise click.UsageError("--types-only, --functions-only, and --kind require --entities")
    if stats and not tree:
        raise click.UsageError("--stats requires --tree")
    if depth is not None and not tree:
        raise click.UsageError("--depth requires --tree")

    if tree:
        # Build tree structure
        tree_root = build_module_tree(
            spec.modules,
            types=spec.types if entities else None,
            functions=spec.functions if entities else None,
            include_internal=internal,
            max_depth=depth,
            types_only=types_only,
            functions_only=functions_only,
            kind_filter=kind_filter,
        )

        if tree_root is None:
            if ctx.text or output_format == "text":
                print("---\n0 modules")
            else:
                envelope = make_envelope(
                    "modules",
                    spec,
                    None,
                    meta={"count": 0, "view": "tree"},
                )
                output_json(envelope, ctx.no_meta)
            return

        # Handle different output formats
        effective_format = output_format or ("text" if ctx.text else "json")

        if effective_format == "text":
            output_text_tree(
                tree_root,
                show_exports=exports,
                show_deps=deps,
                show_entities=entities,
                show_stats=stats,
            )
            return

        if effective_format == "dot":
            _output_tree_dot(tree_root)
            return

        if effective_format == "mermaid":
            _output_tree_mermaid(tree_root)
            return

        # JSON output (default)
        envelope = make_envelope(
            "modules",
            spec,
            tree_root.model_dump(exclude_none=True),
            meta={"count": _count_modules(tree_root), "view": "tree"},
        )
        output_json(envelope, ctx.no_meta)
        return

    # Flat list output (original behavior)
    result: list[ModuleSummary] = []

    for m in spec.modules:
        if not internal and m.internal:
            continue

        result.append(
            ModuleSummary(
                path=m.path,
                description=m.description,
                exports_count=len(m.exports),
                depends_on=m.depends_on,
                internal=m.internal,
            )
        )

    if ctx.text:
        output_text_modules([r.model_dump(exclude_none=True) for r in result])
        return

    envelope = make_envelope(
        "modules",
        spec,
        [r.model_dump(exclude_none=True) for r in result],
        meta={"count": len(result)},
    )
    output_json(envelope, ctx.no_meta)


def _count_modules(node: ModuleTreeNode) -> int:
    """Count real modules in a tree (excluding placeholders)."""
    count = 1 if node.is_package else 0
    for child in node.children:
        count += _count_modules(child)
    return count


def _output_tree_dot(tree: ModuleTreeNode) -> None:
    """Output tree as Graphviz DOT format."""
    print("digraph modules {")
    print("  rankdir=TB;")
    print('  node [shape=box, style=filled, fillcolor=lightblue];')

    def emit_nodes(node: ModuleTreeNode) -> None:
        style = ""
        if node.internal:
            style = ', fillcolor=lightgray, style="filled,dashed"'
        elif not node.is_package:
            style = ", fillcolor=white"
        print(f'  "{node.path}" [label="{node.name}"{style}];')
        for child in node.children:
            emit_nodes(child)

    def emit_edges(node: ModuleTreeNode) -> None:
        for child in node.children:
            print(f'  "{node.path}" -> "{child.path}";')
            emit_edges(child)

    emit_nodes(tree)
    emit_edges(tree)
    print("}")


def _output_tree_mermaid(tree: ModuleTreeNode) -> None:
    """Output tree as Mermaid diagram."""
    print("graph TD")

    def emit_edges(node: ModuleTreeNode) -> None:
        for child in node.children:
            node_id = node.path.replace(".", "_")
            child_id = child.path.replace(".", "_")
            print(f"  {node_id}[{node.name}] --> {child_id}[{child.name}]")
            emit_edges(child)

    emit_edges(tree)


@click.command()
@click.option(
    "--with-implications", is_flag=True, help="Include full implications and anti-patterns"
)
@pass_context
def principles(ctx: Context, with_implications: bool) -> None:
    """
    List design principles.

    \b
    Principles capture design philosophy: why decisions were made,
    what patterns are encouraged, and what anti-patterns to avoid.
    """
    spec = ctx.get_spec()
    result: list[PrincipleSummary] = []

    for p in spec.principles:
        result.append(
            PrincipleSummary(
                id=p.id,
                statement=p.statement,
                has_rationale=bool(p.rationale),
                implications_count=len(p.implications),
                anti_patterns_count=len(p.anti_patterns),
            )
        )

    if ctx.text:
        output_text_principles([r.model_dump(exclude_none=True) for r in result])
        return

    # If with_implications, include full data as dicts
    if with_implications:
        data = [p.model_dump(exclude_none=True) for p in spec.principles]
    else:
        data = [r.model_dump(exclude_none=True) for r in result]

    envelope = make_envelope(
        "principles",
        spec,
        data,
        meta={"count": len(result)},
    )
    output_json(envelope, ctx.no_meta)
