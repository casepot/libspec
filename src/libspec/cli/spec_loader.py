"""Spec file loading and caching."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class LoadedSpec(BaseModel):
    """A loaded and parsed libspec file."""

    path: Path
    data: dict[str, Any]

    class Config:
        arbitrary_types_allowed = True

    @property
    def library(self) -> dict[str, Any]:
        """Get the library object."""
        return self.data.get("library", {})

    @property
    def name(self) -> str:
        """Get library name."""
        return self.library.get("name", "unknown")

    @property
    def version(self) -> str:
        """Get library version."""
        return self.library.get("version", "0.0.0")

    @property
    def extensions(self) -> list[str]:
        """Get enabled extensions."""
        return self.data.get("extensions", [])

    @property
    def types(self) -> list[dict[str, Any]]:
        """Get type definitions."""
        return self.library.get("types", [])

    @property
    def functions(self) -> list[dict[str, Any]]:
        """Get function definitions."""
        return self.library.get("functions", [])

    @property
    def features(self) -> list[dict[str, Any]]:
        """Get feature specifications."""
        return self.library.get("features", [])

    @property
    def modules(self) -> list[dict[str, Any]]:
        """Get module definitions."""
        return self.library.get("modules", [])

    @property
    def principles(self) -> list[dict[str, Any]]:
        """Get design principles."""
        return self.library.get("principles", [])

    @property
    def workflows(self) -> list[dict[str, Any]]:
        """Get workflow definitions (requires lifecycle extension)."""
        return self.library.get("workflows", [])

    @property
    def default_workflow(self) -> str | None:
        """Get default workflow name."""
        return self.library.get("default_workflow")


class SpecLoadError(Exception):
    """Error loading a spec file."""

    pass


def load_spec(path: Path) -> LoadedSpec:
    """
    Load a libspec file from disk.

    Args:
        path: Path to the libspec.json file

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

    return LoadedSpec(path=path, data=data)
