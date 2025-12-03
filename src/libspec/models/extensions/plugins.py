"""Plugins extension models for libspec specifications.

This module defines models for plugin system specifications:
- Plugin interfaces and hooks
- Extension points and lifecycle
- Plugin discovery and loading
"""

from __future__ import annotations

from enum import Enum

from typing import Annotated

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import (
    EntryPointGroup,
    FunctionReference,
    NonEmptyStr,
    PythonNamespaceStr,
    RegexPattern,
    SemVer,
)


class PluginsTypeFields(ExtensionModel):
    extensible: bool | None = Field(
        None, description='Whether this type is an extension point'
    )
    extension_of: str | None = Field(
        None, description='Extension point this type implements'
    )
    plugin_api: bool | None = Field(
        None, description='Whether this type is part of the plugin API'
    )


class Lifecycle(str, Enum):
    """Plugin/extension instance lifecycle.

    - singleton: Single instance for application lifetime
    - per_request: New instance per request/operation
    - transient: New instance on every access
    """

    singleton = 'singleton'
    per_request = 'per_request'
    transient = 'transient'


class ExtensionPointSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Extension point name')
    interface: str | None = Field(None, description='Interface type reference')
    protocol: str | None = Field(None, description='Protocol type reference')
    multiple: bool | None = Field(
        None, description='Whether multiple implementations allowed'
    )
    required: bool | None = Field(
        None, description='Whether at least one implementation required'
    )
    default: str | None = Field(None, description='Default implementation reference')
    priority_ordered: bool | None = Field(
        None, description='Whether implementations are priority ordered'
    )
    lifecycle: Lifecycle | None = Field(None, description='Extension lifecycle')
    version: SemVer | None = Field(None, description='Extension point API version')
    deprecated: bool | None = Field(
        None, description='Whether extension point is deprecated'
    )
    replacement: str | None = Field(None, description='Replacement extension point')
    description: str | None = None


class HookType(str, Enum):
    """Plugin hook mechanism type.

    - filter: Transform data as it passes through
    - action: Side effect with no return value
    - event: Notification broadcast to listeners
    - wrapper: Wrap around original function
    """

    filter = 'filter'
    action = 'action'
    event = 'event'
    wrapper = 'wrapper'


class ExecutionOrder(str, Enum):
    """How multiple hook handlers are executed.

    - sequential: Run handlers one by one in order
    - parallel: Run handlers concurrently
    - pipeline: Each handler output feeds to next
    - first_match: Stop at first handler that returns result
    """

    sequential = 'sequential'
    parallel = 'parallel'
    pipeline = 'pipeline'
    first_match = 'first_match'


class ResultCollection(str, Enum):
    """How results from multiple hook handlers are collected.

    - none: Discard all results
    - first: Return first non-None result
    - last: Return last result
    - all: Return list of all results
    - merge: Merge results (dicts/lists)
    """

    none = 'none'
    first = 'first'
    last = 'last'
    all = 'all'
    merge = 'merge'


class HookParamSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Parameter name')
    type: str = Field(default=..., description='Parameter type')
    mutable: bool | None = Field(None, description='Whether parameter can be modified')
    description: str | None = None


class Validation(str, Enum):
    """When registry entries are validated.

    - none: No validation
    - on_register: Validate when entry is registered
    - on_access: Validate when entry is retrieved
    - both: Validate on both registration and access
    """

    none = 'none'
    on_register = 'on_register'
    on_access = 'on_access'
    both = 'both'


class OverridePolicy(str, Enum):
    """How duplicate registry entries are handled.

    - error: Raise exception on duplicate
    - warn: Log warning and keep original
    - replace_: Replace existing with new entry (named replace_ to avoid shadowing str.replace)
    - ignore: Silently keep original entry
    """

    error = 'error'
    warn = 'warn'
    replace_ = 'replace'  # Avoid shadowing str.replace()
    ignore = 'ignore'


class RegistryMethodsSpec(ExtensionModel):
    register_: str | None = Field(
        None, alias='register', description='Registration method name'
    )
    unregister: str | None = Field(None, description='Unregistration method name')
    get: str | None = Field(None, description='Retrieval method name')
    list: str | None = Field(None, description='List all method name')
    has: str | None = Field(None, description='Check existence method name')


class DiscoveryMechanismType(str, Enum):
    """How plugins are discovered and loaded.

    - entry_points: Python package entry points (setuptools)
    - namespace_packages: Namespace package scanning
    - directory_scan: Filesystem directory scanning
    - config_file: Configuration file listing
    - explicit: Explicit programmatic registration
    - decorator: Decorator-based registration
    """

    entry_points = 'entry_points'
    namespace_packages = 'namespace_packages'
    directory_scan = 'directory_scan'
    config_file = 'config_file'
    explicit = 'explicit'
    decorator = 'decorator'


class DiscoveryMechanismSpec(ExtensionModel):
    type: DiscoveryMechanismType = Field(default=..., description='Discovery mechanism type')
    entry_point_group: EntryPointGroup | None = Field(
        None, description='Entry point group name (for entry_points)'
    )
    namespace: PythonNamespaceStr | None = Field(
        None, description='Package namespace (for namespace_packages)'
    )
    paths: list[str] | None = Field(
        None, description='Directories to scan (for directory_scan)'
    )
    pattern: RegexPattern | None = Field(None, description='File pattern (for directory_scan)')
    config_key: str | None = Field(None, description='Config key (for config_file)')
    decorator: FunctionReference | None = Field(
        None, description='Decorator function (for decorator)'
    )

    @model_validator(mode='after')
    def validate_type_specific_fields(self) -> 'DiscoveryMechanismSpec':
        """Validate type-specific required fields."""
        if self.type == DiscoveryMechanismType.entry_points and not self.entry_point_group:
            raise ValueError(
                "entry_point_group is required when type is 'entry_points'"
            )
        if self.type == DiscoveryMechanismType.namespace_packages and not self.namespace:
            raise ValueError(
                "namespace is required when type is 'namespace_packages'"
            )
        if self.type == DiscoveryMechanismType.directory_scan and not self.paths:
            raise ValueError(
                "paths is required when type is 'directory_scan'"
            )
        return self


class PluginHookRegistration(ExtensionModel):
    hook: str = Field(default=..., description='Hook name')
    handler: FunctionReference = Field(default=..., description='Handler method reference')
    priority: Annotated[int, Field(ge=0)] | None = Field(default=None, description='Handler priority')


class PluginLifecycleSpec(ExtensionModel):
    on_load: FunctionReference | None = Field(None, description='Method called when plugin loads')
    on_enable: FunctionReference | None = Field(
        None, description='Method called when plugin is enabled'
    )
    on_disable: FunctionReference | None = Field(
        None, description='Method called when plugin is disabled'
    )
    on_unload: FunctionReference | None = Field(None, description='Method called when plugin unloads')
    hot_reload: bool | None = Field(
        None, description='Whether plugin supports hot reload'
    )


class HookSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Hook name')
    type: HookType | None = Field(None, description='Hook type')
    signature: str | None = Field(None, description='Hook callback signature')
    parameters: list[HookParamSpec] | None = Field(None, description='Hook parameters')
    returns: str | None = Field(None, description='Return type (for filters)')
    async_: bool | None = Field(
        None, alias='async', description='Whether hook is async'
    )
    execution_order: ExecutionOrder | None = Field(
        None, description='How multiple handlers execute'
    )
    priority_support: bool | None = Field(
        None, description='Whether handlers can specify priority'
    )
    stoppable: bool | None = Field(
        None, description='Whether propagation can be stopped'
    )
    result_collection: ResultCollection | None = Field(
        None, description='How results are collected'
    )
    when: str | None = Field(None, description='When this hook is called')
    description: str | None = None


class RegistrySpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Registry name')
    type: str | None = Field(None, description='Registry class reference')
    key_type: str | None = Field(None, description='Registration key type')
    value_type: str | None = Field(None, description='Registered value type')
    singleton: bool | None = Field(None, description='Whether registry is a singleton')
    thread_safe: bool | None = Field(
        None, description='Whether registry is thread-safe'
    )
    lazy_loading: bool | None = Field(
        None, description='Whether entries are lazily loaded'
    )
    validation: Validation | None = Field(None, description='Entry validation behavior')
    override_policy: OverridePolicy | None = Field(
        None, description='How duplicate registrations are handled'
    )
    methods: RegistryMethodsSpec | None = None
    description: str | None = None


class DiscoverySpec(ExtensionModel):
    mechanisms: list[DiscoveryMechanismSpec] | None = Field(
        None, description='Discovery mechanisms'
    )
    auto_discover: bool | None = Field(
        None, description='Whether auto-discovery is enabled'
    )
    discovery_order: list[str] | None = Field(
        None, description='Order of discovery mechanisms'
    )
    namespace: PythonNamespaceStr | None = Field(None, description='Plugin namespace')


class PluginSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Plugin name')
    version: SemVer | None = Field(None, description='Plugin version')
    type: str | None = Field(None, description='Plugin class reference')
    implements: list[str] | None = Field(
        None, description='Extension points implemented'
    )
    hooks: list[PluginHookRegistration] | None = Field(
        None, description='Hooks this plugin registers'
    )
    dependencies: list[str] | None = Field(None, description='Plugin dependencies')
    conflicts: list[str] | None = Field(None, description='Conflicting plugins')
    priority: Annotated[int, Field(ge=0)] | None = Field(
        default=None, description='Plugin priority (lower = earlier)'
    )
    enabled_by_default: bool | None = Field(
        None, description='Whether plugin is enabled by default'
    )
    config_schema: str | None = Field(
        None, description='Configuration schema reference'
    )
    lifecycle: PluginLifecycleSpec | None = None
    description: str | None = None


class PluginsLibraryFields(ExtensionModel):
    extension_points: list[ExtensionPointSpec] | None = Field(
        None, description='Extension point definitions'
    )
    hooks: list[HookSpec] | None = Field(None, description='Hook definitions')
    registries: list[RegistrySpec] | None = Field(None, description='Plugin registries')
    discovery: DiscoverySpec | None = None
    builtin_plugins: list[PluginSpec] | None = Field(
        None, description='Built-in plugins'
    )
