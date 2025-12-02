"""Spec file loading and caching."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError

from libspec.models import (
    ExtensionName,
    Feature,
    FunctionDef,
    Library,
    LibspecSpec,
    Module,
    Principle,
    TypeDef,
)


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


def load_spec(path: Path, *, validate: bool = True) -> LoadedSpec:
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
        try:
            spec = LibspecSpec.model_validate(data)
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
