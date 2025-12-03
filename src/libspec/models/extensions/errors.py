"""Errors extension models for libspec specifications.

This module defines models for error handling specifications:
- Error types and hierarchies
- Recovery strategies
- Error propagation patterns
"""

from __future__ import annotations

from enum import Enum

from pydantic import Field, HttpUrl

from libspec.models.base import ExtensionModel
from libspec.models.types import NonEmptyStr, TypeAnnotationStr


class ErrorHierarchyNode(ExtensionModel):
    type: NonEmptyStr = Field(default=..., description='Exception class name')
    base: str | None = Field(
        None, description="Base class (e.g., 'Exception', 'RuntimeError')"
    )
    description: str | None = Field(
        None, description='What this exception category represents'
    )
    children: list[str] | None = Field(None, description='Child exception types')


class ExceptionField(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Field name')
    type: TypeAnnotationStr = Field(default=..., description='Field type')
    description: str | None = Field(None, description='What this field contains')


class Severity(str, Enum):
    """Error severity level.

    - info: Informational message, no action needed
    - warning: Potential issue, operation continues
    - error: Operation failed but system stable
    - critical: Severe error, may affect system stability
    """

    info = 'info'
    warning = 'warning'
    error = 'error'
    critical = 'critical'


class ErrorCode(ExtensionModel):
    code: str = Field(default=..., description="Error code (e.g., 'E001', 'AUTH_FAILED')")
    type: str | None = Field(default=None, description='Associated exception type')
    category: str | None = Field(default=None, description='Error category for grouping')
    description: str = Field(default=..., description='Human-readable description')
    docs_url: HttpUrl | None = Field(None, description='URL to detailed documentation')
    severity: Severity | None = Field(None, description='Error severity level')


class ExceptionSpec(ExtensionModel):
    type: NonEmptyStr = Field(default=..., description='Exception class name')
    module: NonEmptyStr = Field(default=..., description='Module where exception is defined')
    base: str | None = Field(None, description='Base exception class')
    description: str | None = Field(None, description='When this exception is raised')
    fields: list[ExceptionField] | None = Field(
        None, description='Exception attributes'
    )
    raised_by: list[str] | None = Field(
        None, description='Functions/methods that raise this exception'
    )
    recovery: str | None = Field(None, description='Recommended recovery strategy')
    retryable: bool | None = Field(
        None, description='Whether the operation can be retried'
    )
    user_facing: bool | None = Field(
        None, description='Whether this error should be shown to end users'
    )
    error_code: str | None = Field(None, description='Associated error code (if any)')


class ErrorsLibraryFields(ExtensionModel):
    error_hierarchy: list[ErrorHierarchyNode] | None = Field(
        None, description='Exception class hierarchy'
    )
    exceptions: list[ExceptionSpec] | None = Field(
        None, description='Detailed exception specifications'
    )
    error_codes: list[ErrorCode] | None = Field(
        None, description='Enumerated error codes'
    )
