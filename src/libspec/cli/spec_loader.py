"""Spec file loading and caching."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any, Dict, Set

from pydantic import BaseModel, ConfigDict, ValidationError

from libspec.models import (
    AsyncFunctionFields,
    AsyncMethodFields,
    AsyncTypeFields,
    CLILibraryFields,
    ConfigLibraryFields,
    DataLibraryFields,
    DataMethodFields,
    DataTypeFields,
    ErrorsLibraryFields,
    EventsLibraryFields,
    EventsMethodFields,
    EventsTypeFields,
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
    ObservabilityLibraryFields,
    ORMLibraryFields,
    ParameterKind,
    PerfFunctionFields,
    PerfMethodFields,
    PerfTypeFields,
    PluginsLibraryFields,
    PluginsTypeFields,
    Principle,
    SafetyFunctionFields,
    SafetyMethodFields,
    SafetyTypeFields,
    StateLibraryFields,
    StateTypeFields,
    TestingLibraryFields,
    TestingTypeFields,
    TypeDef,
    TypeKind,
    VersioningLibraryFields,
    VersioningMethodFields,
    VersioningTypeFields,
    WebLibraryFields,
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

_EXTENSION_VALIDATORS: dict[str, dict[str, type[BaseModel]]] = {
    "async": {
        "method": AsyncMethodFields,
        "function": AsyncFunctionFields,
        "type": AsyncTypeFields,
    },
    "cli": {"library": CLILibraryFields},
    "config": {"library": ConfigLibraryFields},
    "data": {
        "library": DataLibraryFields,
        "method": DataMethodFields,
        "type": DataTypeFields,
    },
    "errors": {"library": ErrorsLibraryFields},
    "events": {
        "library": EventsLibraryFields,
        "method": EventsMethodFields,
        "type": EventsTypeFields,
    },
    "lifecycle": {
        "library": LifecycleLibraryFields,
        "type": LifecycleFields,
        "function": LifecycleFields,
        "feature": LifecycleFields,
        "method": LifecycleFields,
    },
    "observability": {"library": ObservabilityLibraryFields},
    "orm": {"library": ORMLibraryFields},
    "perf": {
        "type": PerfTypeFields,
        "method": PerfMethodFields,
        "function": PerfFunctionFields,
    },
    "plugins": {"library": PluginsLibraryFields, "type": PluginsTypeFields},
    "safety": {
        "type": SafetyTypeFields,
        "method": SafetyMethodFields,
        "function": SafetyFunctionFields,
    },
    "state": {"library": StateLibraryFields, "type": StateTypeFields},
    "testing": {"library": TestingLibraryFields, "type": TestingTypeFields},
    "versioning": {
        "library": VersioningLibraryFields,
        "method": VersioningMethodFields,
        "type": VersioningTypeFields,
    },
    "web": {"library": WebLibraryFields},
}


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


def _iter_methods(type_def: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all method-like entries from a type definition."""

    return [
        *type_def.get("methods", []),
        *type_def.get("class_methods", []),
        *type_def.get("static_methods", []),
    ]


def _ensure_strict_paths(library: dict[str, Any], declared: set[str], context: dict[str, Any]) -> None:
    """In strict mode, enforce that selected path fields reference real files/directories."""

    if not context.get(STRICT_CONTEXT_KEY):
        return

    base_dir = Path(context.get(SPEC_DIR_CONTEXT_KEY, Path.cwd()))

    def _check_path(path_value: str, field: str) -> None:
        candidate = Path(path_value)
        probe = candidate if candidate.is_absolute() else base_dir / candidate
        if not probe.exists():
            raise SpecLoadError(f"{field} must reference an existing file or directory: {path_value}")

    if "testing" in declared:
        coverage = library.get("coverage", {}) or {}
        for target in coverage.get("targets", []) or []:
            path_value = target.get("path")
            if path_value:
                _check_path(path_value, "coverage.targets.path")
        for type_def in library.get("types", []):
            for golden in type_def.get("golden_tests", []) or []:
                _check_path(golden, "testing.golden_tests")

    if "config" in declared:
        sources = library.get("config_sources", {}) or {}
        for loc in sources.get("file_locations", []) or []:
            _check_path(loc, "config.file_locations")

    if "plugins" in declared:
        discovery = library.get("discovery", {}) or {}
        for mechanism in discovery.get("mechanisms", []) or []:
            for directory in mechanism.get("directories", []) or []:
                _check_path(directory, "plugins.discovery.directories")

    if "orm" in declared:
        migrations = library.get("migrations", {}) or {}
        directory = migrations.get("directory")
        if directory:
            _check_path(directory, "orm.migrations.directory")


STRICT_BOOL_KEYS = {
    "async",
    "awaitable",
    "blocking",
    "deterministic",
    "idempotent",
    "jitter",
    "pure",
    "retryable",
}


def _has_extension_fields(entity: dict[str, Any], model_cls: type[BaseModel]) -> bool:
    """Return True when the entity includes any fields defined by the model."""

    if not isinstance(entity, dict):
        return False
    for name, field in model_cls.model_fields.items():
        if name in entity:
            return True
        alias = field.alias
        if alias and alias in entity:
            return True
    return False


def _enforce_strict_scalars(payload: Any) -> None:
    """Recursively enforce strict booleans for risky flags when in strict mode."""

    def _walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                new_path = f"{path}.{key}" if path else key
                if key in STRICT_BOOL_KEYS and item is not None and not isinstance(item, bool):
                    raise SpecLoadError(
                        f"{new_path} must be a boolean when strict models are enabled"
                    )
                _walk(item, new_path)
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                _walk(item, f"{path}[{idx}]" if path else str(idx))

    _walk(payload)


def _validate_extension_payloads(data: dict[str, Any], declared: set[str], context: dict[str, Any]) -> None:
    """Run extension-level validation for declared extensions in strict mode."""

    if not declared:
        return

    library = data.get("library", {})
    strict_flag = bool(context.get(STRICT_CONTEXT_KEY))

    for ext in declared:
        scopes = _EXTENSION_VALIDATORS.get(ext)
        if not scopes:
            continue

        library_model = scopes.get("library")
        if library_model is not None and _has_extension_fields(library, library_model):
            if strict_flag:
                _enforce_strict_scalars(library)
            library_model.model_validate(library, strict=False, context=context)

        type_model = scopes.get("type")
        method_model = scopes.get("method")
        if type_model is not None or method_model is not None:
            for type_def in library.get("types", []):
                if type_model is not None and _has_extension_fields(type_def, type_model):
                    if strict_flag:
                        _enforce_strict_scalars(type_def)
                    type_model.model_validate(type_def, strict=False, context=context)
                if method_model is not None:
                    for method in _iter_methods(type_def):
                        if _has_extension_fields(method, method_model):
                            if strict_flag:
                                _enforce_strict_scalars(method)
                            method_model.model_validate(method, strict=False, context=context)

        function_model = scopes.get("function")
        if function_model is not None:
            for func in library.get("functions", []):
                if _has_extension_fields(func, function_model):
                    if strict_flag:
                        _enforce_strict_scalars(func)
                    function_model.model_validate(func, strict=False, context=context)

        feature_model = scopes.get("feature")
        if feature_model is not None:
            for feature in library.get("features", []):
                if _has_extension_fields(feature, feature_model):
                    if strict_flag:
                        _enforce_strict_scalars(feature)
                    feature_model.model_validate(feature, strict=False, context=context)

    _ensure_strict_paths(library, declared, context)


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
