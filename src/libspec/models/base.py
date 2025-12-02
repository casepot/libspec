"""Base model configuration for all libspec types."""

from pydantic import BaseModel, ConfigDict


class LibspecModel(BaseModel):
    """Base model for all libspec types.

    Provides common configuration:
    - extra="forbid": Catch typos in spec files
    - str_strip_whitespace: Clean up string inputs
    - validate_default: Ensure defaults are valid
    - use_enum_values: Serialize enums as their values
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
        populate_by_name=True,  # Allow both field name and alias
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
        use_enum_values=True,
        populate_by_name=True,
    )


class ExtensionModel(LibspecModel):
    """Base model for extension-specific field containers.

    Uses extra="ignore" to allow additional extension-specific fields.
    """

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
        validate_default=True,
        use_enum_values=True,
        populate_by_name=True,
    )
