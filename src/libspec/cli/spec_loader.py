"""Spec file loading and caching."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, Set

from pydantic import BaseModel, ConfigDict, ValidationError

from libspec.models import (
    ExtensionName,
    Feature,
    FeatureStatus,
    FunctionDef,
    FunctionKind,
    LifecycleFields,
    LifecycleLibraryFields,
    Library,
    LibspecSpec,
    Module,
    ParameterKind,
    Principle,
    TypeDef,
    TypeKind,
)
from libspec.models.utils import SPEC_DIR_CONTEXT_KEY, STRICT_CONTEXT_KEY


class LoadedSpec(BaseModel):
    """A loaded and parsed libspec file.

    This class wraps a LibspecSpec model with convenience accessors
    and path information for CLI usage.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    path: Path
    spec: LibspecSpec

    # Keep raw data for backward compatibility with query commands
    _raw_data: dict[str, Any] | None = None

    @property
    def data(self) -> dict[str, Any]:
        """Get the raw spec data (for backward compatibility with query commands)."""
        if self._raw_data is not None:
            return self._raw_data
        # Serialize spec back to dict if raw data wasn't saved
        return self.spec.model_dump(by_alias=True, exclude_none=True)

    @property
    def library(self) -> Library:
        """Get the library object."""
        return self.spec.library

    @property
    def name(self) -> str:
        """Get library name."""
        return self.spec.library.name

    @property
    def version(self) -> str:
        """Get library version."""
        return self.spec.library.version

    @property
    def extensions(self) -> list[str]:
        """Get enabled extensions."""
        return [e.value if isinstance(e, ExtensionName) else e for e in self.spec.extensions]

    @property
    def types(self) -> list[TypeDef]:
        """Get type definitions."""
        return self.spec.library.types

    @property
    def functions(self) -> list[FunctionDef]:
        """Get function definitions."""
        return self.spec.library.functions

    @property
    def features(self) -> list[Feature]:
        """Get feature specifications."""
        return self.spec.library.features

    @property
    def modules(self) -> list[Module]:
        """Get module definitions."""
        return self.spec.library.modules

    @property
    def principles(self) -> list[Principle]:
        """Get design principles."""
        return self.spec.library.principles

    @property
    def workflows(self) -> list[dict[str, Any]]:
        """Get workflow definitions (requires lifecycle extension).

        Returns raw dicts for backward compatibility with lifecycle command.
        """
        if self._raw_data is not None:
            library = self._raw_data.get("library", {})
            workflows: list[dict[str, Any]] = library.get("workflows", [])
            return workflows
        return []

    @property
    def default_workflow(self) -> str | None:
        """Get default workflow name."""
        if self._raw_data is not None:
            library = self._raw_data.get("library", {})
            default: str | None = library.get("default_workflow")
            return default
        return None


class SpecLoadError(Exception):
    """Error loading a spec file."""

    pass


def _load_extension_field_index() -> dict[str, dict[str, set[str]]]:
    """Build a map of extension-specific fields by location.

    The map structure is {extension: {scope: {fields}}} where scope is one of
    "library", "type", "function", "feature", or "method". Data comes from
    the packaged extension schemas so we stay in sync when schemas change.
    """

    schema_dir = Path(files("libspec") / "schema" / "extensions")
    index: dict[str, dict[str, set[str]]] = {}

    for schema_path in sorted(schema_dir.glob("*.schema.json")):
        try:
            data = json.loads(schema_path.read_text())
        except OSError:
            continue
        ext_name = schema_path.stem
        if ext_name.endswith(".schema"):
            ext_name = ext_name.replace(".schema", "")
        defs: Dict[str, Any] = data.get("$defs", {})
        scopes: dict[str, set[str]] = {
            "library": set(),
            "type": set(),
            "function": set(),
            "feature": set(),
            "method": set(),
        }
        for name, schema in defs.items():
            props = set(schema.get("properties", {}).keys())
            if name.endswith("LibraryFields"):
                scopes["library"].update(props)
            if name.endswith("TypeFields"):
                scopes["type"].update(props)
            if name.endswith("FunctionFields"):
                scopes["function"].update(props)
            if name.endswith("FeatureFields"):
                scopes["feature"].update(props)
            if name.endswith("MethodFields"):
                scopes["method"].update(props)
        if any(scopes.values()):
            index[ext_name] = scopes
    return index


_EXTENSION_FIELD_INDEX = _load_extension_field_index()


def _coerce_enums(data: dict[str, Any]) -> dict[str, Any]:
    """Convert string enum values to Enum instances for strict validation."""

    data = json.loads(json.dumps(data))  # deep copy without mutating caller

    if "extensions" in data:
        data["extensions"] = [ExtensionName(e) for e in data.get("extensions", [])]

    lib = data.get("library", {})

    for type_def in lib.get("types", []):
        if "kind" in type_def:
            type_def["kind"] = TypeKind(type_def["kind"])
        for method_list_key in ("methods", "class_methods", "static_methods"):
            for method in type_def.get(method_list_key, []):
                for param in method.get("parameters", []):
                    if "kind" in param:
                        param["kind"] = ParameterKind(param["kind"])

    for func in lib.get("functions", []):
        if "kind" in func:
            func["kind"] = FunctionKind(func["kind"])
        for param in func.get("parameters", []):
            if "kind" in param:
                param["kind"] = ParameterKind(param["kind"])

    for feature in lib.get("features", []):
        if "status" in feature:
            feature["status"] = FeatureStatus(feature["status"])

    return data


def _validate_extension_payloads(data: dict[str, Any], declared: set[str], context: dict[str, Any]) -> None:
    """Run extension-level validation for selected extensions in strict mode."""

    if "lifecycle" in declared:
        library = data.get("library", {})

        lib_fields = {
            key: library[key]
            for key in LifecycleLibraryFields.model_fields
            if key in library
        }
        if lib_fields:
            LifecycleLibraryFields.model_validate(
                lib_fields, strict=context.get(STRICT_CONTEXT_KEY, False), context=context
            )

        lifecycle_keys = set(LifecycleFields.model_fields.keys())
        for collection_key in ("types", "functions", "features"):
            for entity in library.get(collection_key, []):
                payload = {k: entity[k] for k in lifecycle_keys if k in entity}
                if payload:
                    LifecycleFields.model_validate(
                        payload,
                        strict=context.get(STRICT_CONTEXT_KEY, False),
                        context=context,
                    )


def _ensure_no_extra_fields_when_extensions_absent(data: dict[str, Any]) -> None:
    """In strict mode, reject unexpected fields when no extensions are enabled."""
    extensions: list[str] = data.get("extensions", []) or []
    if extensions:
        return  # Extensions declared; allow extra fields for forward compatibility

    core_type_fields = set(TypeDef.model_fields.keys())
    core_func_fields = set(FunctionDef.model_fields.keys())
    core_feature_fields = set(Feature.model_fields.keys())
    core_module_fields = set(Module.model_fields.keys())
    core_principle_fields = set(Principle.model_fields.keys())

    for i, type_def in enumerate(data.get("library", {}).get("types", [])):
        extra = set(type_def.keys()) - core_type_fields
        if extra:
            raise SpecLoadError(
                f"Unexpected fields in type '{type_def.get('name', '?')}': {sorted(extra)} "
                "(no extensions declared; use --strict-models to enforce this check)"
            )
    for i, fn in enumerate(data.get("library", {}).get("functions", [])):
        extra = set(fn.keys()) - core_func_fields
        if extra:
            raise SpecLoadError(
                f"Unexpected fields in function '{fn.get('name', '?')}': {sorted(extra)} "
                "(no extensions declared; use --strict-models to enforce this check)"
            )
    for i, feat in enumerate(data.get("library", {}).get("features", [])):
        extra = set(feat.keys()) - core_feature_fields
        if extra:
            raise SpecLoadError(
                f"Unexpected fields in feature '{feat.get('id', '?')}': {sorted(extra)} "
                "(no extensions declared; use --strict-models to enforce this check)"
            )
    for mod in data.get("library", {}).get("modules", []):
        extra = set(mod.keys()) - core_module_fields
        if extra:
            raise SpecLoadError(
                f"Unexpected fields in module '{mod.get('path', '?')}': {sorted(extra)} "
                "(no extensions declared; use --strict-models to enforce this check)"
            )
    for principle in data.get("library", {}).get("principles", []):
        extra = set(principle.keys()) - core_principle_fields
        if extra:
            raise SpecLoadError(
                f"Unexpected fields in principle '{principle.get('id', '?')}': {sorted(extra)} "
                "(no extensions declared; use --strict-models to enforce this check)"
            )


def _ensure_extension_fields_declared(data: dict[str, Any], declared: Set[str]) -> None:
    """Reject known extension fields when the extension isn't declared (strict)."""

    library = data.get("library", {})

    def _raise(ext: str, field: str, owner: str) -> None:
        raise SpecLoadError(
            f"Field '{field}' requires '{ext}' extension on {owner} (strict models enabled)"
        )

    for ext, scopes in _EXTENSION_FIELD_INDEX.items():
        if ext in declared:
            continue

        for field in scopes.get("library", set()):
            if field in library:
                _raise(ext, field, "library")

        for type_def in library.get("types", []):
            for field in scopes.get("type", set()):
                if field in type_def:
                    _raise(ext, field, f"type '{type_def.get('name', '?')}'")
            for method in (
                type_def.get("methods", [])
                + type_def.get("class_methods", [])
                + type_def.get("static_methods", [])
            ):
                for field in scopes.get("method", set()):
                    if field in method:
                        _raise(ext, field, f"method '{method.get('name', '?')}'")

        for func in library.get("functions", []):
            for field in scopes.get("function", set()):
                if field in func:
                    _raise(ext, field, f"function '{func.get('name', '?')}'")

        for feature in library.get("features", []):
            for field in scopes.get("feature", set()):
                if field in feature:
                    _raise(ext, field, f"feature '{feature.get('id', '?')}'")


def _ensure_uniqueness(spec: LibspecSpec) -> None:
    """Enforce uniqueness of type names, feature ids, and module paths."""
    types = [t.name for t in spec.library.types]
    features = [f.id for f in spec.library.features]
    modules = [m.path for m in spec.library.modules]

    def _first_duplicate(items: list[str]) -> str | None:
        seen: set[str] = set()
        for item in items:
            if item in seen:
                return item
            seen.add(item)
        return None

    dup_type = _first_duplicate(types)
    if dup_type:
        raise SpecLoadError(f"Duplicate type name '{dup_type}' found (strict models enabled)")
    dup_feat = _first_duplicate(features)
    if dup_feat:
        raise SpecLoadError(f"Duplicate feature id '{dup_feat}' found (strict models enabled)")
    dup_mod = _first_duplicate(modules)
    if dup_mod:
        raise SpecLoadError(f"Duplicate module path '{dup_mod}' found (strict models enabled)")


def load_spec(path: Path, *, validate: bool = True, strict: bool = False) -> LoadedSpec:
    """
    Load a libspec file from disk.

    Args:
        path: Path to the libspec.json file
        validate: If True, validate using Pydantic models. If False, do minimal validation.

    Returns:
        LoadedSpec with parsed data

    Raises:
        SpecLoadError: If the file cannot be loaded or parsed
    """
    if not path.exists():
        raise SpecLoadError(f"Spec file not found: {path}")

    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise SpecLoadError(f"Invalid JSON in {path}: {e}")
    except OSError as e:
        raise SpecLoadError(f"Cannot read {path}: {e}")

    if not isinstance(data, dict):
        raise SpecLoadError(f"Spec must be a JSON object, got {type(data).__name__}")

    if "library" not in data:
        raise SpecLoadError("Spec must have a 'library' field")

    if validate:
        declared_extensions: set[str] = set(data.get("extensions", []) or [])

        if strict:
            _ensure_extension_fields_declared(data, declared_extensions)
            _ensure_no_extra_fields_when_extensions_absent(data)
        try:
            context = {STRICT_CONTEXT_KEY: strict, SPEC_DIR_CONTEXT_KEY: path.parent}
            payload = _coerce_enums(data) if strict else data
            if strict:
                _validate_extension_payloads(payload, declared_extensions, context)
            spec = LibspecSpec.model_validate(
                payload,
                strict=strict,
                context=context,
            )
            if strict:
                _ensure_uniqueness(spec)
        except ValidationError as e:
            # Format validation errors nicely
            errors = []
            for err in e.errors():
                loc = ".".join(str(x) for x in err["loc"])
                msg = err["msg"]
                errors.append(f"  {loc}: {msg}")
            raise SpecLoadError("Invalid spec:\n" + "\n".join(errors))
    else:
        # Minimal validation - just wrap the data
        spec = LibspecSpec.model_construct(**data)

    loaded = LoadedSpec(path=path, spec=spec)
    # Store raw data for backward compatibility
    object.__setattr__(loaded, "_raw_data", data)
    return loaded
