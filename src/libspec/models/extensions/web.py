"""Web extension models for libspec specifications.

This module defines models for web framework specifications:
- HTTP endpoints and routing
- Request/response handling
- Middleware and authentication
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import Field, conint

from libspec.models.base import ExtensionModel


class Method(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    field_ = '*'


class Auth(Enum):
    required = 'required'
    optional = 'optional'
    none = 'none'


class PathParamSpec(ExtensionModel):
    name: str = Field(..., description='Parameter name in path')
    type: str = Field(..., description='Parameter type')
    description: str | None = None
    pattern: str | None = Field(None, description='Regex pattern for validation')


class QueryParamSpec(ExtensionModel):
    name: str = Field(..., description='Query parameter name')
    type: str = Field(..., description='Parameter type')
    required: bool | None = False
    default: str | None = Field(None, description='Default value')
    description: str | None = None
    multiple: bool | None = Field(False, description='Whether multiple values allowed')


class HeaderSpec(ExtensionModel):
    name: str = Field(..., description='Header name')
    type: str | None = Field(None, description='Value type')
    required: bool | None = False
    description: str | None = None


class RequestBodySpec(ExtensionModel):
    type: str | None = Field(None, description='Request body model type')
    content_type: str | None = Field(
        'application/json', description='Expected content type'
    )
    required: bool | None = True
    description: str | None = None


class ResponseSpec(ExtensionModel):
    type: str | None = Field(None, description='Response model type')
    status: conint(ge=100, le=599) | None = Field(200, description='HTTP status code')
    content_type: str | None = Field(
        'application/json', description='Response content type'
    )
    headers: list[HeaderSpec] | None = Field(None, description='Response headers')
    description: str | None = None


class ErrorResponseSpec(ExtensionModel):
    status: conint(ge=100, le=599) = Field(..., description='HTTP status code')
    type: str | None = Field(None, description='Error response model type')
    exception: str | None = Field(
        None, description='Exception type that triggers this response'
    )
    when: str | None = Field(None, description='When this error occurs')
    description: str | None = None


class AppliesTo(Enum):
    all = 'all'
    tagged = 'tagged'
    specific = 'specific'


class Position(Enum):
    before = 'before'
    after = 'after'
    wrap = 'wrap'


class MiddlewareSpec(ExtensionModel):
    name: str = Field(..., description='Middleware name')
    type: str | None = Field(None, description='Middleware class/function reference')
    order: conint(ge=0) | None = Field(
        None, description='Execution order (lower = earlier)'
    )
    applies_to: AppliesTo | None = Field(
        None, description='Which routes this applies to'
    )
    tags: list[str] | None = Field(
        None, description="Tags to match (if applies_to='tagged')"
    )
    routes: list[str] | None = Field(
        None, description="Route paths (if applies_to='specific')"
    )
    position: Position | None = Field(None, description='When middleware runs')
    config: dict[str, Any] | None = Field(None, description='Middleware configuration')
    description: str | None = None


class Scope(Enum):
    request = 'request'
    session = 'session'
    app = 'app'
    singleton = 'singleton'


class DependencySpec(ExtensionModel):
    name: str = Field(..., description='Dependency name')
    type: str = Field(..., description='Dependency type')
    factory: str | None = Field(None, description='Factory function reference')
    scope: Scope | None = Field(None, description='Dependency lifetime')
    cacheable: bool | None = Field(True, description='Whether result can be cached')
    async_: bool | None = Field(
        None, alias='async', description='Whether factory is async'
    )
    dependencies: list[str] | None = Field(
        None, description='Other dependencies this requires'
    )
    description: str | None = None


class Direction(Enum):
    client_to_server = 'client_to_server'
    server_to_client = 'server_to_client'
    bidirectional = 'bidirectional'


class WSMessageSpec(ExtensionModel):
    name: str = Field(..., description='Message type name')
    direction: Direction
    type: str | None = Field(None, description='Message payload type')
    description: str | None = None


class ErrorHandlerSpec(ExtensionModel):
    exception: str = Field(..., description='Exception type to handle')
    status: conint(ge=100, le=599) = Field(..., description='HTTP status code')
    response_type: str | None = Field(None, description='Response model type')
    handler: str | None = Field(None, description='Custom handler function')


class RateLimitSpec(ExtensionModel):
    requests: conint(ge=1) | None = Field(
        None, description='Number of requests allowed'
    )
    window: str | None = Field(None, description="Time window (e.g., '1m', '1h')")
    key: str | None = Field(None, description="Rate limit key (e.g., 'ip', 'user')")
    burst: conint(ge=1) | None = Field(None, description='Burst allowance')


class RouteSpec(ExtensionModel):
    path: str = Field(..., description="URL path pattern (e.g., '/users/{user_id}')")
    method: Method = Field(..., description='HTTP method')
    handler: str | None = Field(None, description='Handler function reference')
    name: str | None = Field(None, description='Route name for URL generation')
    path_params: list[PathParamSpec] | None = Field(
        None, description='Path parameter definitions'
    )
    query_params: list[QueryParamSpec] | None = Field(
        None, description='Query parameter definitions'
    )
    headers: list[HeaderSpec] | None = Field(
        None, description='Required/optional header definitions'
    )
    request_body: RequestBodySpec | None = None
    response: ResponseSpec | None = None
    errors: list[ErrorResponseSpec] | None = Field(None, description='Error responses')
    auth: Auth | None = Field(None, description='Authentication requirement')
    permissions: list[str] | None = Field(None, description='Required permissions')
    rate_limit: RateLimitSpec | None = None
    tags: list[str] | None = Field(None, description='OpenAPI tags')
    deprecated: bool | None = Field(
        None, description='Whether this route is deprecated'
    )
    summary: str | None = Field(None, description='Short summary for OpenAPI')
    description: str | None = Field(None, description='Detailed description')


class WebSocketSpec(ExtensionModel):
    path: str = Field(..., description='WebSocket endpoint path')
    handler: str | None = Field(None, description='Handler function reference')
    subprotocols: list[str] | None = Field(None, description='Supported subprotocols')
    auth: Auth | None = None
    message_types: list[WSMessageSpec] | None = Field(
        None, description='Message type definitions'
    )
    description: str | None = None


class WebLibraryFields(ExtensionModel):
    routes: list[RouteSpec] | None = Field(None, description='HTTP route definitions')
    middleware: list[MiddlewareSpec] | None = Field(
        None, description='Middleware stack'
    )
    dependencies: list[DependencySpec] | None = Field(
        None, description='Dependency injection definitions'
    )
    websockets: list[WebSocketSpec] | None = Field(
        None, description='WebSocket endpoint definitions'
    )
    error_handlers: list[ErrorHandlerSpec] | None = Field(
        None, description='Exception to HTTP response mappings'
    )
