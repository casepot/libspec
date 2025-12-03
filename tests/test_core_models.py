"""Tests for core model validators.

This module tests Pydantic validators for core libspec models:
- ReturnSpec type narrowing (TypeGuard/TypeIs)
- Export origin validation
- DeprecationInfo model
- GenericParam kind-specific validation
"""

import pytest
from pydantic import ValidationError

from libspec.models import (
    Export,
    FunctionDef,
    GenericParam,
    Method,
    ReturnSpec,
)
from libspec.models.core import DeprecationInfo
from libspec.models.types import ExportOrigin, GenericParamKind, GenericVariance


class TestReturnSpecNarrowing:
    """Test ReturnSpec TypeGuard/TypeIs narrowing validation.

    PEP 647 (TypeGuard) and PEP 742 (TypeIs) provide type narrowing.
    The ReturnSpec model tracks these with narrows_type and narrowing_kind.
    """

    def test_valid_type_guard(self) -> None:
        """TypeGuard with both fields specified should validate."""
        ret = ReturnSpec(
            type="TypeGuard[int]",
            description="Returns True if value is int",
            narrows_type="int",
            narrowing_kind="type_guard",
        )
        assert ret.narrows_type == "int"
        assert ret.narrowing_kind == "type_guard"

    def test_valid_type_is(self) -> None:
        """TypeIs with both fields specified should validate."""
        ret = ReturnSpec(
            type="TypeIs[str]",
            description="Returns True if value is str",
            narrows_type="str",
            narrowing_kind="type_is",
        )
        assert ret.narrows_type == "str"
        assert ret.narrowing_kind == "type_is"

    def test_narrowing_fields_must_be_together(self) -> None:
        """narrows_type without narrowing_kind should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ReturnSpec(
                type="TypeGuard[int]",
                narrows_type="int",
                # missing narrowing_kind
            )
        assert "narrows_type and narrowing_kind must be specified together" in str(
            exc_info.value
        )

    def test_narrowing_kind_without_narrows_type(self) -> None:
        """narrowing_kind without narrows_type should fail."""
        with pytest.raises(ValidationError) as exc_info:
            ReturnSpec(
                type="TypeGuard[int]",
                narrowing_kind="type_guard",
                # missing narrows_type
            )
        assert "narrows_type and narrowing_kind must be specified together" in str(
            exc_info.value
        )

    def test_plain_return_spec_without_narrowing(self) -> None:
        """Plain return spec without narrowing fields should validate."""
        ret = ReturnSpec(
            type="bool",
            description="Returns a boolean",
        )
        assert ret.narrows_type is None
        assert ret.narrowing_kind is None

    def test_return_spec_with_python_added(self) -> None:
        """Return spec can track Python version for type narrowing."""
        ret = ReturnSpec(
            type="TypeIs[int]",
            narrows_type="int",
            narrowing_kind="type_is",
            python_added="3.13",
        )
        assert ret.python_added == "3.13"


class TestExportOriginValidation:
    """Test Export model origin validation.

    Exports can have three origins:
    - defined: Symbol is defined in this module
    - reexported: Symbol is imported and re-exported (same name)
    - aliased: Symbol is re-exported under a different name
    """

    def test_defined_export_no_source(self) -> None:
        """Defined exports should not have source_module or source_name."""
        export = Export(
            name="MyClass",
            origin=ExportOrigin.DEFINED,
        )
        assert export.origin == ExportOrigin.DEFINED
        assert export.source_module is None

    def test_defined_export_with_source_module_fails(self) -> None:
        """Defined exports with source_module should fail."""
        with pytest.raises(ValidationError) as exc_info:
            Export(
                name="MyClass",
                origin=ExportOrigin.DEFINED,
                source_module="other.module",
            )
        assert "origin='defined' should not have source_module" in str(exc_info.value)

    def test_reexported_requires_source_module(self) -> None:
        """Reexported symbols must specify source_module."""
        with pytest.raises(ValidationError) as exc_info:
            Export(
                name="MyClass",
                origin=ExportOrigin.REEXPORTED,
                # missing source_module
            )
        assert "origin='reexported' must specify source_module" in str(exc_info.value)

    def test_reexported_with_source_name_fails(self) -> None:
        """Reexported symbols should not have source_name (use aliased instead)."""
        with pytest.raises(ValidationError) as exc_info:
            Export(
                name="MyClass",
                origin=ExportOrigin.REEXPORTED,
                source_module="other.module",
                source_name="OriginalName",  # should use aliased
            )
        assert "should not have source_name" in str(exc_info.value)

    def test_valid_reexport(self) -> None:
        """Valid reexport with source_module."""
        export = Export(
            name="MyClass",
            origin=ExportOrigin.REEXPORTED,
            source_module="other.module",
        )
        assert export.source_module == "other.module"

    def test_aliased_requires_source_module_and_name(self) -> None:
        """Aliased exports must have both source_module and source_name."""
        with pytest.raises(ValidationError) as exc_info:
            Export(
                name="NewName",
                origin=ExportOrigin.ALIASED,
                source_module="other.module",
                # missing source_name
            )
        assert "origin='aliased' must specify source_name" in str(exc_info.value)

    def test_valid_aliased_export(self) -> None:
        """Valid aliased export with source_module and source_name."""
        export = Export(
            name="NewName",
            origin=ExportOrigin.ALIASED,
            source_module="other.module",
            source_name="OriginalName",
        )
        assert export.name == "NewName"
        assert export.source_name == "OriginalName"


class TestDeprecationInfo:
    """Test DeprecationInfo model for PEP 702 @deprecated support."""

    def test_empty_deprecation_info(self) -> None:
        """Deprecation info with no fields is valid."""
        info = DeprecationInfo()
        assert info.message is None
        assert info.since is None

    def test_full_deprecation_info(self) -> None:
        """Deprecation info with all fields."""
        info = DeprecationInfo(
            message="Use new_function instead",
            since="1.0.0",
            removal="2.0.0",
            replacement="#/functions/new_function",
        )
        assert info.message == "Use new_function instead"
        assert info.since == "1.0.0"
        assert info.removal == "2.0.0"
        assert info.replacement == "#/functions/new_function"

    def test_method_with_deprecation(self) -> None:
        """Method can have deprecation info."""
        method = Method(
            name="old_method",
            signature="(self) -> None",
            description="Deprecated method",
            deprecation=DeprecationInfo(
                message="Use new_method instead",
                since="1.0.0",
            ),
        )
        assert method.deprecation is not None
        assert method.deprecation.message == "Use new_method instead"

    def test_method_with_is_override(self) -> None:
        """Method can have is_override flag (PEP 698)."""
        method = Method(
            name="process",
            signature="(self) -> None",
            description="Overridden method",
            is_override=True,
        )
        assert method.is_override is True

    def test_function_with_deprecation(self) -> None:
        """FunctionDef can have deprecation info."""
        func = FunctionDef(
            name="old_func",
            module="mymodule",
            signature="() -> None",
            deprecation=DeprecationInfo(
                message="Deprecated",
                replacement="#/functions/new_func",
            ),
        )
        assert func.deprecation is not None
        assert func.deprecation.replacement == "#/functions/new_func"


class TestGenericParamValidation:
    """Test GenericParam kind-specific validation.

    GenericParam supports three kinds:
    - type_var: Standard TypeVar (PEP 484)
    - param_spec: ParamSpec (PEP 612, Python 3.10+)
    - type_var_tuple: TypeVarTuple (PEP 646, Python 3.11+)
    """

    def test_type_var_with_bound(self) -> None:
        """TypeVar can have a bound constraint."""
        param = GenericParam(
            name="T",
            kind=GenericParamKind.TYPE_VAR,
            bound="Comparable",
        )
        assert param.bound == "Comparable"

    def test_type_var_with_constraints(self) -> None:
        """TypeVar can have type constraints."""
        param = GenericParam(
            name="T",
            kind=GenericParamKind.TYPE_VAR,
            constraints=["int", "str"],
        )
        assert param.constraints == ["int", "str"]

    def test_type_var_with_variance(self) -> None:
        """TypeVar can have variance."""
        param = GenericParam(
            name="T_co",
            kind=GenericParamKind.TYPE_VAR,
            variance=GenericVariance.COVARIANT,
        )
        assert param.variance == GenericVariance.COVARIANT

    def test_param_spec_no_bound(self) -> None:
        """ParamSpec does not support bound constraint."""
        with pytest.raises(ValidationError) as exc_info:
            GenericParam(
                name="P",
                kind=GenericParamKind.PARAM_SPEC,
                bound="SomeType",
            )
        assert "ParamSpec does not support 'bound'" in str(exc_info.value)

    def test_param_spec_no_variance(self) -> None:
        """ParamSpec does not support variance."""
        with pytest.raises(ValidationError) as exc_info:
            GenericParam(
                name="P",
                kind=GenericParamKind.PARAM_SPEC,
                variance=GenericVariance.COVARIANT,
            )
        assert "ParamSpec does not support variance" in str(exc_info.value)

    def test_param_spec_no_constraints(self) -> None:
        """ParamSpec does not support type constraints."""
        with pytest.raises(ValidationError) as exc_info:
            GenericParam(
                name="P",
                kind=GenericParamKind.PARAM_SPEC,
                constraints=["int", "str"],
            )
        assert "ParamSpec does not support type constraints" in str(exc_info.value)

    def test_valid_param_spec(self) -> None:
        """Valid ParamSpec with default (PEP 696)."""
        param = GenericParam(
            name="P",
            kind=GenericParamKind.PARAM_SPEC,
            default="[int, str]",
        )
        assert param.kind == GenericParamKind.PARAM_SPEC
        assert param.default == "[int, str]"

    def test_type_var_tuple_no_bound(self) -> None:
        """TypeVarTuple does not support bound constraint."""
        with pytest.raises(ValidationError) as exc_info:
            GenericParam(
                name="Ts",
                kind=GenericParamKind.TYPE_VAR_TUPLE,
                bound="SomeType",
            )
        assert "TypeVarTuple does not support 'bound'" in str(exc_info.value)

    def test_type_var_tuple_no_variance(self) -> None:
        """TypeVarTuple does not support variance."""
        with pytest.raises(ValidationError) as exc_info:
            GenericParam(
                name="Ts",
                kind=GenericParamKind.TYPE_VAR_TUPLE,
                variance=GenericVariance.COVARIANT,
            )
        assert "TypeVarTuple does not support explicit variance" in str(exc_info.value)

    def test_valid_type_var_tuple(self) -> None:
        """Valid TypeVarTuple."""
        param = GenericParam(
            name="Ts",
            kind=GenericParamKind.TYPE_VAR_TUPLE,
        )
        assert param.kind == GenericParamKind.TYPE_VAR_TUPLE

    def test_generic_param_with_python_added(self) -> None:
        """GenericParam can track Python version."""
        param = GenericParam(
            name="P",
            kind=GenericParamKind.PARAM_SPEC,
            python_added="3.10",
        )
        assert param.python_added == "3.10"
