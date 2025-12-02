"""Tests for Pydantic validators matching lint rule behavior.

These tests verify that the Pydantic model validators produce the same
validation results as the corresponding lint rules. This ensures that
validation behavior is consistent whether specs are validated via
Pydantic models (at load time) or via lint rules (explicit linting).
"""

import pytest
from pydantic import ValidationError

from libspec.models import (
    Feature,
    FunctionDef,
    Library,
    LibspecSpec,
    Principle,
    TypeDef,
)
from libspec.models.types import (
    KebabCaseId,
    PascalCaseName,
    ScreamingSnakeCase,
    SnakeCaseId,
)


class TestKebabCaseId:
    """Test KebabCaseId pattern matches N001/N002 lint rules."""

    @pytest.mark.parametrize(
        "valid_id",
        [
            "feature",
            "my-feature",
            "my-feature-id",
            "a",
            "a1",
            "feature1",
            "my-feature-123",
            "x-y-z",
        ],
    )
    def test_valid_kebab_case(self, valid_id: str) -> None:
        """Valid kebab-case IDs should pass validation."""
        # Test via Feature.id which uses KebabCaseId
        feature = Feature(
            id=valid_id,
            category="TEST",
            steps=["step1"],
        )
        assert feature.id == valid_id

    @pytest.mark.parametrize(
        "invalid_id",
        [
            "MyFeature",  # PascalCase
            "my_feature",  # snake_case
            "MY-FEATURE",  # uppercase
            "-feature",  # leading hyphen
            "feature-",  # trailing hyphen
            "my--feature",  # double hyphen
            "123feature",  # starts with number
            "",  # empty
        ],
    )
    def test_invalid_kebab_case(self, invalid_id: str) -> None:
        """Invalid kebab-case IDs should fail validation."""
        with pytest.raises(ValidationError):
            Feature(
                id=invalid_id,
                category="TEST",
                steps=["step1"],
            )


class TestPascalCaseName:
    """Test PascalCaseName pattern matches N003 lint rule."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "MyClass",
            "A",
            "ABC",
            "MyClass123",
            "HTTPClient",
            "XMLParser",
        ],
    )
    def test_valid_pascal_case(self, valid_name: str) -> None:
        """Valid PascalCase names should pass validation."""
        type_def = TypeDef(
            name=valid_name,
            kind="class",
            module="mymodule",
            docstring="A test type",
            methods=[{"name": "test", "signature": "() -> None", "description": "Test"}],
        )
        assert type_def.name == valid_name

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "myClass",  # camelCase
            "my_class",  # snake_case
            "my-class",  # kebab-case
            "MY_CLASS",  # SCREAMING_SNAKE
            "123Class",  # starts with number
            "",  # empty
        ],
    )
    def test_invalid_pascal_case(self, invalid_name: str) -> None:
        """Invalid PascalCase names should fail validation."""
        with pytest.raises(ValidationError):
            TypeDef(
                name=invalid_name,
                kind="class",
                module="mymodule",
                docstring="A test type",
                methods=[{"name": "test", "signature": "() -> None", "description": "Test"}],
            )


class TestSnakeCaseId:
    """Test SnakeCaseId pattern matches N004 lint rule."""

    @pytest.mark.parametrize(
        "valid_name",
        [
            "my_function",
            "a",
            "abc",
            "my_func_123",
            "get_data",
            "x_y_z",
        ],
    )
    def test_valid_snake_case(self, valid_name: str) -> None:
        """Valid snake_case names should pass validation."""
        func = FunctionDef(
            name=valid_name,
            module="mymodule",
            signature="() -> None",
        )
        assert func.name == valid_name

    @pytest.mark.parametrize(
        "invalid_name",
        [
            "MyFunction",  # PascalCase
            "myFunction",  # camelCase
            "my-function",  # kebab-case
            "MY_FUNCTION",  # SCREAMING_SNAKE
            "_private",  # leading underscore (not dunder)
            "func_",  # trailing underscore
            "my__func",  # double underscore (not dunder)
            "123func",  # starts with number
        ],
    )
    def test_invalid_snake_case(self, invalid_name: str) -> None:
        """Invalid snake_case names should fail validation."""
        with pytest.raises(ValidationError):
            FunctionDef(
                name=invalid_name,
                module="mymodule",
                signature="() -> None",
            )

    @pytest.mark.parametrize(
        "dunder_name",
        [
            "__init__",
            "__str__",
            "__repr__",
            "__call__",
            "__getitem__",
        ],
    )
    def test_dunder_methods_allowed(self, dunder_name: str) -> None:
        """Dunder methods should be allowed per N004 exception."""
        func = FunctionDef(
            name=dunder_name,
            module="mymodule",
            signature="() -> None",
        )
        assert func.name == dunder_name


class TestScreamingSnakeCase:
    """Test ScreamingSnakeCase pattern matches N006 lint rule."""

    @pytest.mark.parametrize(
        "valid_category",
        [
            "CORE",
            "MY_CATEGORY",
            "A",
            "ABC",
            "FEATURE_123",
            "X_Y_Z",
        ],
    )
    def test_valid_screaming_snake(self, valid_category: str) -> None:
        """Valid SCREAMING_SNAKE_CASE should pass validation."""
        feature = Feature(
            id="test-feature",
            category=valid_category,
            steps=["step1"],
        )
        assert feature.category == valid_category

    @pytest.mark.parametrize(
        "invalid_category",
        [
            "core",  # lowercase
            "MyCategory",  # PascalCase
            "my_category",  # snake_case
            "MY-CATEGORY",  # kebab-case
            "_CATEGORY",  # leading underscore
            "CATEGORY_",  # trailing underscore
            "MY__CATEGORY",  # double underscore
            "123CATEGORY",  # starts with number
        ],
    )
    def test_invalid_screaming_snake(self, invalid_category: str) -> None:
        """Invalid SCREAMING_SNAKE_CASE should fail validation."""
        with pytest.raises(ValidationError):
            Feature(
                id="test-feature",
                category=invalid_category,
                steps=["step1"],
            )


class TestTypeDefValidators:
    """Test TypeDef model validators matching C005/C006 lint rules."""

    def test_c005_enum_must_have_values(self) -> None:
        """C005: Enum types must have values defined."""
        with pytest.raises(ValidationError) as exc_info:
            TypeDef(
                name="MyEnum",
                kind="enum",
                module="mymodule",
                docstring="An empty enum",
                values=[],  # Empty values
            )
        assert "must have values defined" in str(exc_info.value)

    def test_c005_enum_with_values_passes(self) -> None:
        """Enum with values should pass validation."""
        enum_type = TypeDef(
            name="Status",
            kind="enum",
            module="mymodule",
            docstring="Status enum",
            values=[
                {"name": "ACTIVE", "value": 1},
                {"name": "INACTIVE", "value": 2},
            ],
        )
        assert enum_type.name == "Status"
        assert len(enum_type.values) == 2

    def test_c006_protocol_must_have_methods_or_properties(self) -> None:
        """C006: Protocol types must have methods or properties."""
        with pytest.raises(ValidationError) as exc_info:
            TypeDef(
                name="EmptyProtocol",
                kind="protocol",
                module="mymodule",
                docstring="An empty protocol",
                methods=[],
                properties=[],
            )
        assert "must have methods or properties" in str(exc_info.value)

    def test_c006_protocol_with_methods_passes(self) -> None:
        """Protocol with methods should pass validation."""
        protocol = TypeDef(
            name="Readable",
            kind="protocol",
            module="mymodule",
            docstring="A readable protocol",
            methods=[
                {"name": "read", "signature": "(self) -> bytes", "description": "Read data"},
            ],
        )
        assert protocol.name == "Readable"

    def test_c006_protocol_with_properties_passes(self) -> None:
        """Protocol with properties should pass validation."""
        protocol = TypeDef(
            name="Named",
            kind="protocol",
            module="mymodule",
            docstring="A named protocol",
            properties=[
                {"name": "name", "type": "str", "description": "The name"},
            ],
        )
        assert protocol.name == "Named"

    def test_class_without_methods_allowed(self) -> None:
        """Regular classes can be empty (only enum/protocol require members)."""
        # Note: S007 lint rule warns about empty types, but it's not a hard error
        cls = TypeDef(
            name="Empty",
            kind="class",
            module="mymodule",
            docstring="An empty class",
            methods=[],
            properties=[],
        )
        assert cls.name == "Empty"


class TestLibspecSpecValidation:
    """Test full spec validation."""

    def test_minimal_valid_spec(self) -> None:
        """Minimal valid spec should parse without errors."""
        spec = LibspecSpec(
            library=Library(
                name="mylib",
                version="0.1.0",
            )
        )
        assert spec.library.name == "mylib"

    def test_spec_with_invalid_type_name_fails(self) -> None:
        """Spec with invalid type name should fail validation."""
        with pytest.raises(ValidationError):
            LibspecSpec(
                library=Library(
                    name="mylib",
                    version="0.1.0",
                    types=[
                        {
                            "name": "invalid_name",  # Not PascalCase
                            "kind": "class",
                            "module": "mylib",
                            "docstring": "Test",
                            "methods": [{"name": "test", "signature": "() -> None", "description": "Test"}],
                        }
                    ],
                )
            )

    def test_spec_with_invalid_feature_id_fails(self) -> None:
        """Spec with invalid feature ID should fail validation."""
        with pytest.raises(ValidationError):
            LibspecSpec(
                library=Library(
                    name="mylib",
                    version="0.1.0",
                    features=[
                        {
                            "id": "Invalid_Feature",  # Not kebab-case
                            "category": "CORE",
                            "steps": ["step1"],
                        }
                    ],
                )
            )

    def test_spec_with_all_valid_entities(self) -> None:
        """Spec with all valid entities should parse successfully."""
        spec = LibspecSpec(
            library=Library(
                name="mylib",
                version="1.0.0",
                types=[
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "mylib",
                        "docstring": "A test class",
                        "methods": [
                            {
                                "name": "do_something",
                                "signature": "(self) -> None",
                                "description": "Do something",
                            }
                        ],
                    }
                ],
                functions=[
                    {
                        "name": "helper_func",
                        "module": "mylib",
                        "signature": "() -> None",
                    }
                ],
                features=[
                    {
                        "id": "my-feature",
                        "category": "CORE",
                        "steps": ["Test step"],
                    }
                ],
                principles=[
                    {
                        "id": "my-principle",
                        "statement": "Keep it simple",
                    }
                ],
            )
        )
        assert len(spec.library.types) == 1
        assert len(spec.library.functions) == 1
        assert len(spec.library.features) == 1
        assert len(spec.library.principles) == 1
