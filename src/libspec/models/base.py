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

    All libspec models inherit common configuration:
    - extra="forbid": Reject unknown fields (catches typos)
    - str_strip_whitespace: Auto-strip string whitespace
    - validate_default/validate_assignment: Always validate
    - use_enum_values: Serialize enums as string values
    - populate_by_name: Accept both field names and aliases
    - serialize_by_alias: Output uses alias names (async_ → async)
    - from_attributes: Support ORM/dataclass conversion

    Validation Context:
        Models support context-aware validation via model_validate():

        - strict_models (bool): When True, enables strict type checking.
          Disables type coercion (e.g., int 1 won't become bool True).
          Used by StrictBool fields to reject non-boolean values.

        - spec_dir (Path): Base directory for resolving relative paths.
          Used by path validators to check file existence.

        Example:
            spec = LibspecSpec.model_validate(
                data,
                context={"strict_models": True, "spec_dir": Path("/project")}
            )
    """

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,  # Allow both field name and alias
        serialize_by_alias=True,  # Output uses alias names (async_ → async)
        from_attributes=True,  # Enable validation from dataclasses/ORM
    )


class ExtensibleModel(LibspecModel):
    """Base model for types that can have extension fields.

    Uses extra="ignore" to allow extension fields (e.g., workflow_state)
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
        serialize_by_alias=True,
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
        serialize_by_alias=True,
        from_attributes=True,
    )
