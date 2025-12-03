"""Output formatting for CLI commands."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from libspec.cli.models.output import ModuleTreeNode, OutputEnvelope, SpecContext
from libspec.cli.spec_loader import LoadedSpec

if TYPE_CHECKING:
    from libspec.models import Module


def make_envelope(
    command: str,
    spec: LoadedSpec,
    result: Any,
    meta: dict[str, Any] | None = None,
) -> OutputEnvelope[Any]:
    """Create a standard output envelope."""
    return OutputEnvelope(
        command=command,
        spec=SpecContext(
            path=str(spec.path),
            library=spec.name,
            version=spec.version,
        ),
        result=result,
        meta=meta or {},
    )


def output_json(envelope: OutputEnvelope[Any], no_meta: bool = False) -> None:
    """Output envelope as JSON."""
    data = envelope.model_dump(mode="json", exclude_none=True)
    if no_meta:
        data.pop("meta", None)
    print(json.dumps(data, indent=2))


def output_text_types(types: list[dict[str, Any]]) -> None:
    """Output type list in text format."""
    for t in types:
        kind = t.get("kind", "?")
        name = t.get("name", "?")
        module = t.get("module", "?")
        print(f"TYPE {kind} {name} {module}")
    print("---")
    print(f"{len(types)} types")


def output_text_functions(functions: list[dict[str, Any]]) -> None:
    """Output function list in text format."""
    for f in functions:
        kind = f.get("kind", "function")
        name = f.get("name", "?")
        module = f.get("module", "?")
        print(f"FUNC {kind} {name} {module}")
    print("---")
    print(f"{len(functions)} functions")


def output_text_features(features: list[dict[str, Any]]) -> None:
    """Output feature list in text format."""
    for f in features:
        status = f.get("status", "planned")
        fid = f.get("id", "?")
        category = f.get("category", "?")
        print(f"FEAT {status} {fid} {category}")
    print("---")
    print(f"{len(features)} features")


def output_text_modules(modules: list[dict[str, Any]]) -> None:
    """Output module list in text format."""
    for m in modules:
        path = m.get("path", "?")
        internal = "internal" if m.get("internal") else "public"
        deps = len(m.get("depends_on", []))
        print(f"MOD {internal} {path} deps:{deps}")
    print("---")
    print(f"{len(modules)} modules")


def output_text_principles(principles: list[dict[str, Any]]) -> None:
    """Output principles list in text format."""
    for p in principles:
        pid = p.get("id", "?")
        stmt = p.get("statement", "")[:60]
        print(f"PRINC {pid} {stmt}")
    print("---")
    print(f"{len(principles)} principles")


def output_text_info(
    spec: LoadedSpec,
    counts: dict[str, int],
    coverage: dict[str, Any],
) -> None:
    """Output info in text format."""
    lib = spec.library
    print(f"{lib.name} {lib.version}")
    if spec.extensions:
        print(f"ext: {','.join(spec.extensions)}")
    print(
        f"types: {counts.get('types', 0)} | "
        f"funcs: {counts.get('functions', 0)} | "
        f"features: {counts.get('features', 0)}"
    )
    feat_total = coverage.get("features_total", 0)
    if feat_total > 0:
        tested = coverage.get("features_tested", 0)
        impl = coverage.get("features_implemented", 0)
        print(f"coverage: {impl}/{feat_total} implemented, {tested}/{feat_total} tested")


def output_text_lint(issues: list[dict[str, Any]], passed: bool) -> None:
    """Output lint results in text format."""
    for issue in issues:
        sev = issue.get("severity", "?")[0].upper()  # E/W/I
        rule = issue.get("rule", "?")
        msg = issue.get("message", "")
        path = issue.get("path", "")
        print(f"{sev} {rule} {path} {msg}")
    print("---")
    status = "PASS" if passed else "FAIL"
    print(f"{status} {len(issues)} issues")


def output_text_validate(errors: list[str], valid: bool) -> None:
    """Output validation results in text format."""
    for err in errors:
        print(f"ERR {err}")
    print("---")
    status = "VALID" if valid else "INVALID"
    print(f"{status} {len(errors)} errors")


def build_module_tree(
    modules: list[Module],
    include_internal: bool = False,
) -> ModuleTreeNode | None:
    """Build a tree structure from flat module list.

    Args:
        modules: Flat list of Module objects
        include_internal: Whether to include internal modules

    Returns:
        Root node of the tree, or None if no modules
    """
    if not modules:
        return None

    # Filter modules
    filtered = [m for m in modules if include_internal or not m.internal]
    if not filtered:
        return None

    # Create a dict of path -> module data
    module_data: dict[str, Module] = {m.path: m for m in filtered}

    # Find the common root (shortest common prefix)
    paths = sorted(module_data.keys())
    if not paths:
        return None

    # Get root package name (first component of shortest path)
    root_name = paths[0].split(".")[0]

    # Build tree nodes for all paths
    nodes: dict[str, ModuleTreeNode] = {}

    def get_or_create_node(path: str) -> ModuleTreeNode:
        """Get existing node or create a placeholder."""
        if path in nodes:
            return nodes[path]

        parts = path.split(".")
        name = parts[-1]

        # Check if this is a real module or a placeholder
        mod = module_data.get(path)
        if mod:
            # Get export names
            exports: list[str] = []
            for exp in mod.exports:
                if isinstance(exp, str):
                    exports.append(exp)
                else:
                    exports.append(exp.name)

            node = ModuleTreeNode(
                name=name,
                path=path,
                exports=exports,
                depends_on=mod.depends_on,
                internal=mod.internal,
                is_package=True,
            )
        else:
            # Placeholder node (intermediate package not in spec)
            node = ModuleTreeNode(
                name=name,
                path=path,
                is_package=False,
            )

        nodes[path] = node
        return node

    # Create all nodes and build parent-child relationships
    for path in paths:
        get_or_create_node(path)

        # Create intermediate nodes and link to parents
        parts = path.split(".")
        for i in range(1, len(parts)):
            parent_path = ".".join(parts[:i])
            child_path = ".".join(parts[: i + 1])

            parent_node = get_or_create_node(parent_path)
            child_node = get_or_create_node(child_path)

            if child_node not in parent_node.children:
                parent_node.children.append(child_node)

    # Sort children alphabetically at each level
    def sort_children(node: ModuleTreeNode) -> None:
        node.children.sort(key=lambda n: n.name)
        for child in node.children:
            sort_children(child)

    root = nodes.get(root_name)
    if root:
        sort_children(root)

    return root


def output_text_tree(
    tree: ModuleTreeNode,
    show_exports: bool = False,
    show_deps: bool = False,
) -> int:
    """Output module tree in ASCII format.

    Args:
        tree: Root node of the tree
        show_exports: Whether to show export names
        show_deps: Whether to show dependencies

    Returns:
        Count of modules displayed
    """
    count = 0

    def render_node(
        node: ModuleTreeNode,
        prefix: str = "",
        is_last: bool = True,
        is_root: bool = False,
    ) -> None:
        nonlocal count

        # Build the line for this node
        if is_root:
            line = ""
        else:
            connector = "└── " if is_last else "├── "
            line = f"{prefix}{connector}"

        # Module name with trailing slash for packages
        name_part = f"{node.name}/"

        # Add internal marker
        if node.internal:
            name_part += " (internal)"

        # Add exports if requested
        if show_exports and node.exports:
            exports_str = ", ".join(node.exports[:5])
            if len(node.exports) > 5:
                exports_str += f", ... +{len(node.exports) - 5}"
            name_part += f" [{exports_str}]"

        # Add deps if requested
        if show_deps and node.depends_on:
            deps_str = ", ".join(node.depends_on)
            name_part += f" → {deps_str}"
        elif show_deps and node.is_package:
            name_part += " → (no deps)"

        line += name_part
        print(line)

        if node.is_package:
            count += 1

        # Render children
        if is_root:
            child_prefix = ""
        else:
            child_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(node.children):
            is_last_child = i == len(node.children) - 1
            render_node(child, child_prefix, is_last_child, is_root=False)

    render_node(tree, is_root=True)
    print("---")
    print(f"{count} modules")
    return count
