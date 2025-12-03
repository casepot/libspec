"""Config extension models for libspec specifications.

This module defines models for configuration management:
- Configuration sources and formats
- Environment variable mappings
- Validation rules and defaults
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import (
    CliFlag,
    EnvVarName,
    EnvVarPrefix,
    LocalPath,
    NonEmptyStr,
    ShortFlag,
)


class SettingSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Setting name')
    type: str = Field(
        default=..., description='Setting type (str, int, float, bool, list, dict)'
    )
    default: Any | None = Field(None, description='Default value')
    env_var: EnvVarName | None = Field(None, description='Environment variable name')
    cli_flag: CliFlag | None = Field(None, description="CLI flag (e.g., '--timeout')")
    cli_short: ShortFlag | None = Field(None, description="Short CLI flag (e.g., '-t')")
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
    choices: list[Any] | None = Field(
        default=None, description='Valid choices for enum-like settings'
    )

    @model_validator(mode='after')
    def validate_setting_consistency(self) -> 'SettingSpec':
        """Validate setting configuration consistency."""
        import warnings

        if self.required is True and self.default is not None:
            raise ValueError(
                f"Setting '{self.name}' is required but has a default value"
            )
        if self.deprecated is True and not self.deprecated_message:
            warnings.warn(
                f"Setting '{self.name}' is deprecated but has no deprecated_message",
                UserWarning,
                stacklevel=2,
            )
        return self


class PriorityEnum(str, Enum):
    """Configuration source priority order.

    - cli: Command-line arguments (highest priority)
    - env: Environment variables
    - file: Configuration files
    - defaults: Default values
    - remote: Remote configuration server
    - secrets_manager: Secrets management service
    """

    cli = 'cli'
    env = 'env'
    file = 'file'
    defaults = 'defaults'
    remote = 'remote'
    secrets_manager = 'secrets_manager'


class FileFormat(str, Enum):
    """Configuration file format.

    - toml: TOML format (pyproject.toml style)
    - yaml: YAML format
    - json: JSON format
    - ini: INI/ConfigParser format
    - env: .env file format
    """

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
    paths: list[LocalPath] | None = Field(
        None, description='Config file search paths'
    )
    file_name_pattern: str | None = Field(
        None, description="Config file name pattern (e.g., '{name}.toml')"
    )
    env_prefix: EnvVarPrefix | None = Field(
        None, description="Environment variable prefix (e.g., 'MYLIB_')"
    )
    nested_delimiter: str | None = Field(
        '__', description='Delimiter for nested settings in env vars'
    )


class ProfileSpec(ExtensionModel):
    name: NonEmptyStr = Field(
        default=..., description="Profile name (e.g., 'development', 'production')"
    )
    description: str | None = Field(None, description='What this profile is for')
    inherits: str | None = Field(None, description='Base profile to inherit from')
    overrides: dict[str, Any] | None = Field(
        None, description='Setting overrides for this profile'
    )
    env_var_trigger: EnvVarName | None = Field(
        None, description='Env var that activates this profile'
    )


class SecretsStorage(str, Enum):
    """Where secrets are stored and retrieved from.

    - env: Environment variables
    - keyring: System keyring (keyring library)
    - vault: HashiCorp Vault
    - aws_secrets: AWS Secrets Manager
    - gcp_secrets: Google Cloud Secret Manager
    - azure_keyvault: Azure Key Vault
    - file: Local encrypted file
    """

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
