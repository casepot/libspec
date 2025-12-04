"""Tests for maturity tracking and requirement dependencies.

This module tests the EntityMaturity enum and Requirement model:
- EntityMaturity enum values and usage on entities
- Requirement model with CrossReference and min_maturity
- maturity and requires fields on TypeDef, FunctionDef, Feature, Method
"""

import pytest
from pydantic import ValidationError

from libspec.models import (
    EntityMaturity,
    Feature,
    FunctionDef,
    Method,
    Requirement,
    TypeDef,
)
from libspec.models.types import FunctionKind, TypeKind


class TestEntityMaturity:
    """Test EntityMaturity enum values."""

    def test_all_maturity_stages_exist(self) -> None:
        """All 8 maturity stages should be defined."""
        stages = [
            EntityMaturity.IDEA,
            EntityMaturity.SPECIFIED,
            EntityMaturity.DESIGNED,
            EntityMaturity.IMPLEMENTED,
            EntityMaturity.TESTED,
            EntityMaturity.DOCUMENTED,
            EntityMaturity.RELEASED,
            EntityMaturity.DEPRECATED,
        ]
        assert len(stages) == 8
        assert len(EntityMaturity) == 8

    def test_maturity_string_values(self) -> None:
        """Maturity enum values should be lowercase strings."""
        assert EntityMaturity.IDEA.value == "idea"
        assert EntityMaturity.SPECIFIED.value == "specified"
        assert EntityMaturity.DESIGNED.value == "designed"
        assert EntityMaturity.IMPLEMENTED.value == "implemented"
        assert EntityMaturity.TESTED.value == "tested"
        assert EntityMaturity.DOCUMENTED.value == "documented"
        assert EntityMaturity.RELEASED.value == "released"
        assert EntityMaturity.DEPRECATED.value == "deprecated"


class TestRequirement:
    """Test Requirement model for dependency tracking."""

    def test_minimal_requirement(self) -> None:
        """Requirement with just ref should be valid."""
        req = Requirement(ref="#/types/Connection")
        assert req.ref == "#/types/Connection"
        assert req.min_maturity is None
        assert req.reason is None

    def test_requirement_with_min_maturity(self) -> None:
        """Requirement can specify minimum maturity level."""
        req = Requirement(
            ref="#/types/Connection",
            min_maturity=EntityMaturity.DESIGNED,
        )
        assert req.min_maturity == EntityMaturity.DESIGNED

    def test_requirement_with_reason(self) -> None:
        """Requirement can include explanation."""
        req = Requirement(
            ref="#/functions/validate_input",
            reason="Needed for input handling",
        )
        assert req.reason == "Needed for input handling"

    def test_requirement_with_all_fields(self) -> None:
        """Requirement with all fields populated."""
        req = Requirement(
            ref="#/types/MessageCodec",
            min_maturity=EntityMaturity.IMPLEMENTED,
            reason="Codec must exist before handler can process messages",
        )
        assert req.ref == "#/types/MessageCodec"
        assert req.min_maturity == EntityMaturity.IMPLEMENTED
        assert "Codec must exist" in req.reason

    def test_invalid_cross_reference_fails(self) -> None:
        """Requirement with invalid ref format should fail."""
        with pytest.raises(ValidationError):
            Requirement(ref="invalid-ref")

    def test_requirement_accepts_function_ref(self) -> None:
        """Requirement can reference functions."""
        req = Requirement(ref="#/functions/parse_data")
        assert req.ref == "#/functions/parse_data"

    def test_requirement_accepts_feature_ref(self) -> None:
        """Requirement can reference features."""
        req = Requirement(ref="#/features/authentication")
        assert req.ref == "#/features/authentication"


class TestTypeDefMaturity:
    """Test maturity and requires fields on TypeDef."""

    def test_typedef_without_maturity(self) -> None:
        """TypeDef without maturity field defaults to None."""
        typedef = TypeDef(
            name="Point",
            kind=TypeKind.CLASS,
            module="geometry.core",
        )
        assert typedef.maturity is None
        assert typedef.requires == []

    def test_typedef_with_maturity(self) -> None:
        """TypeDef can have maturity set."""
        typedef = TypeDef(
            name="Connection",
            kind=TypeKind.CLASS,
            module="network.core",
            maturity=EntityMaturity.DESIGNED,
        )
        assert typedef.maturity == EntityMaturity.DESIGNED

    def test_typedef_with_requirements(self) -> None:
        """TypeDef can have dependency requirements."""
        typedef = TypeDef(
            name="WebSocketHandler",
            kind=TypeKind.CLASS,
            module="network.websocket",
            requires=[
                Requirement(ref="#/types/Connection", min_maturity=EntityMaturity.DESIGNED),
                Requirement(ref="#/types/MessageCodec", min_maturity=EntityMaturity.IMPLEMENTED),
            ],
        )
        assert len(typedef.requires) == 2
        assert typedef.requires[0].ref == "#/types/Connection"
        assert typedef.requires[1].min_maturity == EntityMaturity.IMPLEMENTED


class TestFunctionDefMaturity:
    """Test maturity and requires fields on FunctionDef."""

    def test_functiondef_without_maturity(self) -> None:
        """FunctionDef without maturity defaults to None."""
        func = FunctionDef(
            name="parse_json",
            module="utils.parser",
            signature="(data: str) -> dict",
        )
        assert func.maturity is None
        assert func.requires == []

    def test_functiondef_with_maturity(self) -> None:
        """FunctionDef can have maturity set."""
        func = FunctionDef(
            name="connect",
            module="network.client",
            signature="(host: str, port: int) -> Connection",
            maturity=EntityMaturity.IMPLEMENTED,
        )
        assert func.maturity == EntityMaturity.IMPLEMENTED

    def test_functiondef_with_requirements(self) -> None:
        """FunctionDef can have dependency requirements."""
        func = FunctionDef(
            name="send_message",
            module="network.messaging",
            signature="(conn: Connection, msg: Message) -> None",
            requires=[
                Requirement(ref="#/types/Connection"),
                Requirement(ref="#/types/Message", min_maturity=EntityMaturity.DESIGNED),
            ],
        )
        assert len(func.requires) == 2


class TestFeatureMaturity:
    """Test maturity and requires fields on Feature."""

    def test_feature_without_maturity(self) -> None:
        """Feature without maturity defaults to None."""
        feature = Feature(
            id="user-auth",
            category="SECURITY",
        )
        assert feature.maturity is None
        assert feature.requires == []

    def test_feature_with_maturity(self) -> None:
        """Feature can have maturity set."""
        feature = Feature(
            id="websocket-support",
            category="NETWORKING",
            maturity=EntityMaturity.SPECIFIED,
        )
        assert feature.maturity == EntityMaturity.SPECIFIED

    def test_feature_with_requirements(self) -> None:
        """Feature can have dependency requirements."""
        feature = Feature(
            id="websocket-support",
            category="NETWORKING",
            requires=[
                Requirement(ref="#/types/Connection"),
                Requirement(ref="#/features/basic_networking", min_maturity=EntityMaturity.TESTED),
            ],
        )
        assert len(feature.requires) == 2
        assert feature.requires[1].min_maturity == EntityMaturity.TESTED


class TestMethodMaturity:
    """Test maturity field on Method."""

    def test_method_without_maturity(self) -> None:
        """Method without maturity defaults to None."""
        method = Method(
            name="connect",
            signature="(self) -> None",
        )
        assert method.maturity is None

    def test_method_with_maturity(self) -> None:
        """Method can have maturity set."""
        method = Method(
            name="send",
            signature="(self, data: bytes) -> int",
            maturity=EntityMaturity.IMPLEMENTED,
        )
        assert method.maturity == EntityMaturity.IMPLEMENTED


class TestMaturityIntegration:
    """Integration tests for maturity tracking."""

    def test_full_typedef_with_maturity_tracking(self) -> None:
        """TypeDef with complete maturity and requirements."""
        typedef = TypeDef(
            name="HttpClient",
            kind=TypeKind.CLASS,
            module="http.client",
            docstring="HTTP client for making web requests",
            maturity=EntityMaturity.DESIGNED,
            requires=[
                Requirement(
                    ref="#/types/Connection",
                    min_maturity=EntityMaturity.IMPLEMENTED,
                    reason="Connection pooling required",
                ),
            ],
            methods=[
                Method(
                    name="get",
                    signature="(self, url: str) -> Response",
                    maturity=EntityMaturity.IDEA,
                ),
                Method(
                    name="post",
                    signature="(self, url: str, data: dict) -> Response",
                    maturity=EntityMaturity.DESIGNED,
                ),
            ],
        )
        assert typedef.maturity == EntityMaturity.DESIGNED
        assert len(typedef.requires) == 1
        assert typedef.methods[0].maturity == EntityMaturity.IDEA
        assert typedef.methods[1].maturity == EntityMaturity.DESIGNED

    def test_maturity_serialization(self) -> None:
        """Maturity values serialize correctly to JSON."""
        func = FunctionDef(
            name="process",
            module="core",
            signature="() -> None",
            maturity=EntityMaturity.TESTED,
        )
        data = func.model_dump()
        assert data["maturity"] == "tested"

    def test_maturity_from_string(self) -> None:
        """Maturity can be parsed from string value."""
        data = {
            "name": "Process",
            "kind": "class",
            "module": "core",
            "maturity": "implemented",
        }
        typedef = TypeDef.model_validate(data)
        assert typedef.maturity == EntityMaturity.IMPLEMENTED
