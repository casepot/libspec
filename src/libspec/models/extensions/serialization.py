"""Serialization extension models for libspec specifications.

This module defines models for data serialization specifications:
- Serialization formats and encodings
- Custom type handlers and encoders/decoders
- Schema generation and validation
- Type coercion and mapping rules
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field

from libspec.models.base import ExtensionModel


class SerializationFormat(Enum):
    """Supported serialization formats."""

    json = "json"
    yaml = "yaml"
    toml = "toml"
    msgpack = "msgpack"
    pickle = "pickle"
    protobuf = "protobuf"
    avro = "avro"
    parquet = "parquet"
    xml = "xml"
    csv = "csv"
    custom = "custom"


class EncodingStrategy(Enum):
    """Encoding strategy for complex types."""

    iso8601 = "iso8601"
    timestamp = "timestamp"
    unix_epoch = "unix_epoch"
    base64 = "base64"
    hex = "hex"
    string = "string"
    dict = "dict"
    custom = "custom"


class NamingConvention(Enum):
    """Field naming conventions."""

    snake_case = "snake_case"
    camel_case = "camel_case"
    pascal_case = "pascal_case"
    kebab_case = "kebab_case"
    preserve = "preserve"


class DateTimeFormat(Enum):
    """DateTime serialization format."""

    iso8601 = "iso8601"
    rfc2822 = "rfc2822"
    rfc3339 = "rfc3339"
    unix_timestamp = "unix_timestamp"
    unix_timestamp_ms = "unix_timestamp_ms"
    custom = "custom"


class BinaryEncoding(Enum):
    """Binary data encoding."""

    base64 = "base64"
    base64url = "base64url"
    hex = "hex"
    raw = "raw"


class NullHandling(Enum):
    """How null/None values are handled."""

    include = "include"
    exclude = "exclude"
    use_default = "use_default"


class CircularRefHandling(Enum):
    """How circular references are handled."""

    error = "error"
    ignore = "ignore"
    ref_id = "ref_id"
    max_depth = "max_depth"


class SchemaFormat(Enum):
    """Schema output format."""

    json_schema = "json_schema"
    openapi = "openapi"
    avro_schema = "avro_schema"
    protobuf_schema = "protobuf_schema"
    xml_schema = "xml_schema"
    custom = "custom"


class ValidationMode(Enum):
    """Validation strictness mode."""

    strict = "strict"
    lax = "lax"
    coerce = "coerce"
    none = "none"


class CoercionBehavior(Enum):
    """How type coercion behaves."""

    implicit = "implicit"
    explicit = "explicit"
    error = "error"
    warn = "warn"


class SerializationErrorKind(Enum):
    """Types of serialization errors."""

    encoding_error = "encoding_error"
    decoding_error = "decoding_error"
    validation_error = "validation_error"
    type_error = "type_error"
    circular_ref = "circular_ref"
    missing_field = "missing_field"
    unknown_field = "unknown_field"
    schema_error = "schema_error"


class TypeMappingSpec(ExtensionModel):
    """Mapping between Python types and serialization types."""

    python_type: str = Field(default=..., description="Python type to map")
    serialized_type: str = Field(default=..., description="Type in serialized format")
    bidirectional: bool | None = Field(
        True, description="Whether mapping works both ways"
    )
    encoder: str | None = Field(None, description="Custom encoder function reference")
    decoder: str | None = Field(None, description="Custom decoder function reference")


class CoercionRuleSpec(ExtensionModel):
    """Type coercion rule for deserialization."""

    from_type: str = Field(default=..., description="Source type")
    to_type: str = Field(default=..., description="Target type")
    behavior: CoercionBehavior | None = Field(None, description="Coercion behavior")
    lossy: bool | None = Field(
        None, description="Whether coercion may lose information"
    )
    validator: str | None = Field(None, description="Validation function reference")


class EncoderSpec(ExtensionModel):
    """Custom encoder specification."""

    name: str = Field(default=..., description="Encoder name")
    type: str = Field(default=..., description="Type this encoder handles")
    function: str | None = Field(None, description="Encoder function reference")
    method: str | None = Field(None, description="Encoder method on the type")
    priority: int | None = Field(
        None, ge=0, description="Priority when multiple encoders match"
    )
    description: str | None = None


class DecoderSpec(ExtensionModel):
    """Custom decoder specification."""

    name: str = Field(default=..., description="Decoder name")
    type: str = Field(default=..., description="Type this decoder produces")
    function: str | None = Field(None, description="Decoder function reference")
    factory: str | None = Field(None, description="Factory method on the type")
    priority: int | None = Field(
        None, ge=0, description="Priority when multiple decoders match"
    )
    description: str | None = None


class TypeHandlerSpec(ExtensionModel):
    """Combined encoder/decoder for a type."""

    type: str = Field(default=..., description="Type this handler manages")
    encoder: EncoderSpec | None = None
    decoder: DecoderSpec | None = None
    strategy: EncodingStrategy | None = Field(None, description="Encoding strategy")
    format_hint: str | None = Field(
        None, description="Format hint for custom encodings"
    )


class EncoderRegistrySpec(ExtensionModel):
    """Registry of custom encoders."""

    name: str = Field(default=..., description="Registry name")
    encoders: list[EncoderSpec] | None = Field(None, description="Registered encoders")
    fallback: str | None = Field(None, description="Fallback encoder reference")
    strict: bool | None = Field(
        None, description="Error on unhandled types vs using repr"
    )


class DecoderRegistrySpec(ExtensionModel):
    """Registry of custom decoders."""

    name: str = Field(default=..., description="Registry name")
    decoders: list[DecoderSpec] | None = Field(None, description="Registered decoders")
    fallback: str | None = Field(None, description="Fallback decoder reference")
    strict: bool | None = Field(
        None, description="Error on unhandled types vs returning raw"
    )


class SerializerOptionSpec(ExtensionModel):
    """Configuration option for a serializer."""

    name: str = Field(default=..., description="Option name")
    type: str = Field(default=..., description="Option type")
    default: str | None = Field(None, description="Default value (as string)")
    description: str | None = Field(None, description="What this option controls")
    choices: list[str] | None = Field(None, description="Valid choices")


class SerializerSpec(ExtensionModel):
    """Serializer definition."""

    name: str = Field(default=..., description="Serializer name")
    format: SerializationFormat = Field(default=..., description="Output format")
    type: str | None = Field(None, description="Serializer class reference")
    serialize_method: str | None = Field(
        None, description="Method to serialize objects"
    )
    deserialize_method: str | None = Field(
        None, description="Method to deserialize data"
    )
    options: list[SerializerOptionSpec] | None = Field(
        None, description="Configuration options"
    )
    naming_convention: NamingConvention | None = Field(
        None, description="Field naming convention"
    )
    datetime_format: DateTimeFormat | None = Field(
        None, description="DateTime format"
    )
    binary_encoding: BinaryEncoding | None = Field(
        None, description="Binary data encoding"
    )
    null_handling: NullHandling | None = Field(
        None, description="Null value handling"
    )
    circular_ref_handling: CircularRefHandling | None = Field(
        None, description="Circular reference handling"
    )
    max_depth: int | None = Field(
        None, ge=1, description="Maximum nesting depth"
    )
    indent: int | None = Field(
        None, ge=0, description="Indentation for pretty printing"
    )
    sort_keys: bool | None = Field(
        None, description="Whether to sort dictionary keys"
    )
    ensure_ascii: bool | None = Field(
        None, description="Whether to escape non-ASCII characters"
    )
    type_handlers: list[TypeHandlerSpec] | None = Field(
        None, description="Custom type handlers"
    )
    description: str | None = None


class SchemaFieldSpec(ExtensionModel):
    """Field in a generated schema."""

    name: str = Field(default=..., description="Field name")
    type: str = Field(default=..., description="Field type in schema")
    required: bool | None = Field(True, description="Whether field is required")
    nullable: bool | None = Field(None, description="Whether field can be null")
    default: str | None = Field(None, description="Default value")
    description: str | None = None
    examples: list[str] | None = Field(None, description="Example values")


class SchemaSpec(ExtensionModel):
    """Schema definition for serialization."""

    name: str = Field(default=..., description="Schema name")
    format: SchemaFormat = Field(default=..., description="Schema format")
    type: str | None = Field(None, description="Python type this schema represents")
    version: str | None = Field(None, description="Schema version")
    fields: list[SchemaFieldSpec] | None = Field(None, description="Schema fields")
    generator: str | None = Field(None, description="Schema generator function")
    validator: str | None = Field(None, description="Schema validator function")
    strict: bool | None = Field(
        None, description="Whether unknown fields cause errors"
    )
    description: str | None = None


class SerializationSettingsSpec(ExtensionModel):
    """Global serialization settings."""

    default_format: SerializationFormat | None = Field(
        None, description="Default serialization format"
    )
    validation_mode: ValidationMode | None = Field(
        None, description="Validation strictness"
    )
    coercion_behavior: CoercionBehavior | None = Field(
        None, description="Default coercion behavior"
    )
    naming_convention: NamingConvention | None = Field(
        None, description="Default naming convention"
    )
    datetime_format: DateTimeFormat | None = Field(
        None, description="Default datetime format"
    )
    datetime_custom_format: str | None = Field(
        None, description="Custom datetime format string"
    )
    binary_encoding: BinaryEncoding | None = Field(
        None, description="Default binary encoding"
    )
    encoding: str | None = Field(
        None, description="Text encoding (e.g., 'utf-8')"
    )
    max_string_length: int | None = Field(
        None, ge=1, description="Maximum string length"
    )
    max_collection_size: int | None = Field(
        None, ge=1, description="Maximum collection size"
    )
    max_nesting_depth: int | None = Field(
        None, ge=1, description="Maximum nesting depth"
    )
    pretty_print: bool | None = Field(
        None, description="Whether to pretty print output"
    )


class SerializationErrorSpec(ExtensionModel):
    """Serialization error specification."""

    kind: SerializationErrorKind = Field(default=..., description="Error kind")
    exception: str | None = Field(None, description="Exception class raised")
    message_template: str | None = Field(None, description="Error message template")
    recoverable: bool | None = Field(
        None, description="Whether error is recoverable"
    )


class SerializationPerformanceSpec(ExtensionModel):
    """Performance characteristics of serialization."""

    streaming: bool | None = Field(
        None, description="Whether streaming is supported"
    )
    lazy_loading: bool | None = Field(
        None, description="Whether lazy loading is supported"
    )
    incremental: bool | None = Field(
        None, description="Whether incremental parsing is supported"
    )
    zero_copy: bool | None = Field(
        None, description="Whether zero-copy is possible"
    )
    buffer_size: int | None = Field(
        None, ge=1, description="Default buffer size"
    )
    compression: list[str] | None = Field(
        None, description="Supported compression algorithms"
    )
    estimated_overhead: float | None = Field(
        None, ge=0.0, description="Estimated size overhead ratio"
    )


class SerializationTypeFields(ExtensionModel):
    """Extension fields for types."""

    serializable: bool | None = Field(
        None, description="Whether this type is serializable"
    )
    serialize_as: str | None = Field(
        None, description="Type to serialize as"
    )
    custom_encoder: str | None = Field(
        None, description="Custom encoder for this type"
    )
    custom_decoder: str | None = Field(
        None, description="Custom decoder for this type"
    )
    schema_spec: SchemaSpec | None = Field(
        None, description="Schema specification for this type"
    )
    exclude_fields: list[str] | None = Field(
        None, description="Fields to exclude from serialization"
    )
    include_fields: list[str] | None = Field(
        None, description="Only serialize these fields"
    )
    field_aliases: dict[str, str] | None = Field(
        None, description="Field name aliases for serialization"
    )


class SerializationMethodFields(ExtensionModel):
    """Extension fields for methods."""

    serializes: bool | None = Field(
        None, description="Whether this method serializes data"
    )
    deserializes: bool | None = Field(
        None, description="Whether this method deserializes data"
    )
    format: SerializationFormat | None = Field(
        None, description="Format this method handles"
    )
    streaming: bool | None = Field(
        None, description="Whether method supports streaming"
    )


class SerializationFunctionFields(ExtensionModel):
    """Extension fields for functions."""

    serializes: bool | None = Field(
        None, description="Whether this function serializes data"
    )
    deserializes: bool | None = Field(
        None, description="Whether this function deserializes data"
    )
    format: SerializationFormat | None = Field(
        None, description="Format this function handles"
    )
    streaming: bool | None = Field(
        None, description="Whether function supports streaming"
    )


class SerializationLibraryFields(ExtensionModel):
    """Extension fields for libraries."""

    serializers: list[SerializerSpec] | None = Field(
        None, description="Available serializers"
    )
    schemas: list[SchemaSpec] | None = Field(
        None, description="Schema definitions"
    )
    type_mappings: list[TypeMappingSpec] | None = Field(
        None, description="Type mappings"
    )
    coercion_rules: list[CoercionRuleSpec] | None = Field(
        None, description="Type coercion rules"
    )
    encoder_registry: EncoderRegistrySpec | None = None
    decoder_registry: DecoderRegistrySpec | None = None
    settings: SerializationSettingsSpec | None = None
    errors: list[SerializationErrorSpec] | None = Field(
        None, description="Serialization errors"
    )
    performance: SerializationPerformanceSpec | None = None
