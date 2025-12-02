"""Config extension models for libspec specifications.

This module defines models for configuration management:
- Configuration sources and formats
- Environment variable mappings
- Validation rules and defaults
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field

from libspec.models.base import ExtensionModel


class SettingSpec(ExtensionModel):
    name: str = Field(..., description='Setting name')
    type: str = Field(
        ..., description='Setting type (str, int, float, bool, list, dict)'
    )
    default: Any | None = Field(None, description='Default value')
    env_var: str | None = Field(None, description='Environment variable name')
    cli_flag: str | None = Field(None, description="CLI flag (e.g., '--timeout')")
    cli_short: str | None = Field(None, description="Short CLI flag (e.g., '-t')")
    validation: str | None = Field(
        None, description="Validation rule (e.g., 'gt(0)', 'regex(...)')"
    )
    description: str | None = Field(None, description='What this setting controls')
    required: bool | None = Field(
        False, description='Whether this setting must be provided'
    )
    secret: bool | None = Field(False, description='Whether this is a secret value')
    deprecated: bool | None = Field(
        False, description='Whether this setting is deprecated'
    )
    deprecated_message: str | None = Field(
        None, description='Deprecation message with migration guidance'
    )
    choices: list | None = Field(
        None, description='Valid choices for enum-like settings'
    )


class PriorityEnum(Enum):
    cli = 'cli'
    env = 'env'
    file = 'file'
    defaults = 'defaults'
    remote = 'remote'
    secrets_manager = 'secrets_manager'


class FileFormat(Enum):
    toml = 'toml'
    yaml = 'yaml'
    json = 'json'
    ini = 'ini'
    env = 'env'


class ConfigSourcesSpec(ExtensionModel):
    priority: list[PriorityEnum] | None = Field(
        None, description='Source priority (first = highest)'
    )
    file_formats: list[FileFormat] | None = Field(
        None, description='Supported config file formats'
    )
    file_locations: list[str] | None = Field(
        None, description='Config file search paths'
    )
    file_name_pattern: str | None = Field(
        None, description="Config file name pattern (e.g., '{name}.toml')"
    )
    env_prefix: str | None = Field(
        None, description="Environment variable prefix (e.g., 'MYLIB_')"
    )
    nested_delimiter: str | None = Field(
        '__', description='Delimiter for nested settings in env vars'
    )


class ProfileSpec(ExtensionModel):
    name: str = Field(
        ..., description="Profile name (e.g., 'development', 'production')"
    )
    description: str | None = Field(None, description='What this profile is for')
    inherits: str | None = Field(None, description='Base profile to inherit from')
    overrides: dict[str, Any] | None = Field(
        None, description='Setting overrides for this profile'
    )
    env_var_trigger: str | None = Field(
        None, description='Env var that activates this profile'
    )


class SecretsStorage(Enum):
    env = 'env'
    keyring = 'keyring'
    vault = 'vault'
    aws_secrets = 'aws_secrets'
    gcp_secrets = 'gcp_secrets'
    azure_keyvault = 'azure_keyvault'
    file = 'file'


class SecretsSpec(ExtensionModel):
    fields: list[str] | None = Field(None, description='Setting names that are secrets')
    storage: SecretsStorage | None = Field(None, description='Where secrets are stored')
    masking: bool | None = Field(True, description='Whether secrets are masked in logs')
    rotation_supported: bool | None = Field(
        None, description='Whether secret rotation is supported'
    )


class ConfigLibraryFields(ExtensionModel):
    settings: list[SettingSpec] | None = Field(
        None, description='Configuration settings'
    )
    config_sources: ConfigSourcesSpec | None = None
    profiles: list[ProfileSpec] | None = Field(
        None, description='Configuration profiles'
    )
    secrets: SecretsSpec | None = None
