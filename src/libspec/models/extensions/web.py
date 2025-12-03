"""Web extension models for libspec specifications.

This module defines models for web framework specifications:
- HTTP endpoints and routing
- Request/response handling
- Middleware and authentication
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Annotated, Any

from pydantic import Field, model_validator

from libspec.models.base import ExtensionModel
from libspec.models.types import MimeType, NonEmptyStr, RoutePath, TypeAnnotationStr


class Method(Enum):
    """HTTP request methods.

    Standard methods plus wildcard for matching any method.
    """

    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'
    HEAD = 'HEAD'
    OPTIONS = 'OPTIONS'
    WILDCARD = '*'


class Auth(Enum):
    """Authentication requirement level for a route.

    - required: Authentication is mandatory
    - optional: Route works with or without authentication
    - none: No authentication needed
    """

    required = 'required'
    optional = 'optional'
    none = 'none'


class PathParamSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Parameter name in path')
    type: TypeAnnotationStr = Field(default=..., description='Parameter type')
    description: str | None = None
    pattern: str | None = Field(None, description='Regex pattern for validation')


class QueryParamSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Query parameter name')
    type: TypeAnnotationStr = Field(default=..., description='Parameter type')
    required: bool | None = False
    default: str | None = Field(None, description='Default value')
    description: str | None = None
    multiple: bool | None = Field(False, description='Whether multiple values allowed')


class HeaderSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Header name')
    type: TypeAnnotationStr | None = Field(None, description='Value type')
    required: bool | None = False
    description: str | None = None


class RequestBodySpec(ExtensionModel):
    type: str | None = Field(None, description='Request body model type')
    content_type: MimeType | None = Field(
        'application/json', description='Expected content type'
    )
    required: bool | None = True
    description: str | None = None


class ResponseSpec(ExtensionModel):
    type: str | None = Field(None, description='Response model type')
    status: Annotated[int, Field(ge=100, le=599)] | None = Field(default=200, description='HTTP status code')
    content_type: MimeType | None = Field(
        'application/json', description='Response content type'
    )
    headers: list[HeaderSpec] | None = Field(None, description='Response headers')
    description: str | None = None


class ErrorResponseSpec(ExtensionModel):
    status: Annotated[int, Field(ge=100, le=599)] = Field(default=..., description='HTTP status code')
    type: str | None = Field(None, description='Error response model type')
    exception: str | None = Field(
        None, description='Exception type that triggers this response'
    )
    when: str | None = Field(None, description='When this error occurs')
    description: str | None = None


class AppliesTo(Enum):
    """Which routes middleware applies to.

    - all: Applies to all routes
    - tagged: Applies to routes with matching tags
    - specific: Applies to explicitly listed routes
    """

    all = 'all'
    tagged = 'tagged'
    specific = 'specific'


class Position(Enum):
    """When middleware runs relative to the request handler.

    - before: Runs before the handler
    - after: Runs after the handler
    - wrap: Wraps the handler (runs before and after)
    """

    before = 'before'
    after = 'after'
    wrap = 'wrap'


class MiddlewareSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Middleware name')
    type: str | None = Field(None, description='Middleware class/function reference')
    order: Annotated[int, Field(ge=0)] | None = Field(
        default=None, description='Execution order (lower = earlier)'
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

    @model_validator(mode='after')
    def validate_middleware_config(self) -> 'MiddlewareSpec':
        """Validate applies_to has corresponding tags/routes."""
        if self.applies_to == AppliesTo.tagged and not self.tags:
            raise ValueError("tags required when applies_to='tagged'")
        if self.applies_to == AppliesTo.specific and not self.routes:
            raise ValueError("routes required when applies_to='specific'")
        return self


class Scope(Enum):
    """Dependency injection lifetime scope.

    - request: New instance per HTTP request
    - session: Shared within a user session
    - app: Shared across the application
    - singleton: Single instance for the app lifetime
    """

    request = 'request'
    session = 'session'
    app = 'app'
    singleton = 'singleton'


class DependencySpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Dependency name')
    type: str = Field(default=..., description='Dependency type')
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
    """WebSocket message flow direction.

    - client_to_server: Client sends to server only
    - server_to_client: Server sends to client only
    - bidirectional: Messages flow both ways
    """

    client_to_server = 'client_to_server'
    server_to_client = 'server_to_client'
    bidirectional = 'bidirectional'


class WSMessageSpec(ExtensionModel):
    name: NonEmptyStr = Field(default=..., description='Message type name')
    direction: Direction
    type: str | None = Field(None, description='Message payload type')
    description: str | None = None


class ErrorHandlerSpec(ExtensionModel):
    exception: str = Field(default=..., description='Exception type to handle')
    status: Annotated[int, Field(ge=100, le=599)] = Field(default=..., description='HTTP status code')
    response_type: str | None = Field(None, description='Response model type')
    handler: str | None = Field(None, description='Custom handler function')


class RateLimitSpec(ExtensionModel):
    requests: Annotated[int, Field(ge=1)] | None = Field(
        default=None, description='Number of requests allowed'
    )
    window: str | None = Field(None, description="Time window (e.g., '1m', '1h')")
    key: str | None = Field(None, description="Rate limit key (e.g., 'ip', 'user')")
    burst: Annotated[int, Field(ge=1)] | None = Field(default=None, description='Burst allowance')


class RouteSpec(ExtensionModel):
    path: RoutePath = Field(default=..., description="URL path pattern (e.g., '/users/{user_id}')")
    method: Method = Field(default=..., description='HTTP method')
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

    @model_validator(mode='after')
    def validate_path(self) -> 'RouteSpec':
        """Validate path starts with / and has balanced braces."""
        import warnings

        if not self.path.startswith('/'):
            raise ValueError(f"Route path must start with '/': {self.path!r}")
        # Check balanced braces for path parameters
        open_braces = self.path.count('{')
        close_braces = self.path.count('}')
        if open_braces != close_braces:
            raise ValueError(
                f"Unbalanced braces in path {self.path!r}: "
                f"{open_braces} open, {close_braces} close"
            )
        # Validate path parameter format (alphanumeric + underscore)
        param_pattern = re.compile(r'\{([^}]+)\}')
        params_in_path: set[str] = set()
        for match in param_pattern.finditer(self.path):
            param_name = match.group(1)
            params_in_path.add(param_name)
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', param_name):
                raise ValueError(
                    f"Invalid path parameter name {param_name!r} in {self.path!r}: "
                    "must be a valid identifier"
                )
        # Warn if path params in path are not defined in path_params
        defined_params = {p.name for p in (self.path_params or [])}
        missing = params_in_path - defined_params
        if missing:
            warnings.warn(
                f"Path parameters {missing} in {self.path!r} not defined in path_params",
                UserWarning,
                stacklevel=2,
            )
        return self


class WebSocketSpec(ExtensionModel):
    path: str = Field(default=..., description='WebSocket endpoint path')
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
