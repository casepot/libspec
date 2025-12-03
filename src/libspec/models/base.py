"""Base model configuration for all libspec types.

Validation Modes:
-----------------
- Python: model_validate(dict) with optional coercion
- JSON: model_validate_json(str) for JSON strings
- Strings: model_validate_strings(dict) for string-only dicts

Context Keys (passed via model_validate(..., context={...})):
- strict_models: bool - Disable type coercion, enforce strict booleans
- spec_dir: Path - Base directory for resolving relative paths

Usage:
    # Standard validation with coercion
    spec = LibspecSpec.model_validate(data)

    # Strict mode (no coercion)
    spec = LibspecSpec.model_validate(
        data,
        context={"strict_models": True, "spec_dir": Path("/path/to/spec")}
    )
"""

from pydantic import BaseModel, ConfigDict


class LibspecModel(BaseModel):
    """Base model for all libspec types.

    Provides common configuration:
    - extra="forbid": Catch typos in spec files
    - str_strip_whitespace: Clean up string inputs
    - validate_default: Ensure defaults are valid
    - validate_assignment: Re-validate when fields are modified
    - use_enum_values: Serialize enums as their values
    - from_attributes: Enable validation from dataclasses/ORM objects
    - populate_by_name: Allow both field name and alias
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,  # Allow both field name and alias
        from_attributes=True,  # Enable validation from dataclasses/ORM
    )


class ExtensibleModel(LibspecModel):
    """Base model for types that can have extension fields.

    Uses extra="ignore" to allow extension fields (e.g., lifecycle_state)
    even when the extension is not declared, for forward compatibility.
    This applies to entity types like TypeDef, FunctionDef, Feature, etc.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        from_attributes=True,
    )


class ExtensionModel(LibspecModel):
    """Base model for extension-specific field containers.

    Uses extra="ignore" to allow additional extension-specific fields.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
        from_attributes=True,
    )
