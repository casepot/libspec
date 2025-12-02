"""Tests for version lint rules (V001-V005).

This module tests:
- V004: Generic parameter version features (enhanced for PEP 696 defaults)
- V005: Exception group version features (new rule)
"""

import pytest

from libspec.cli.lint.rules.version import (
    ExceptionGroupVersionFeatures,
    GenericParamVersionFeatures,
)


class TestGenericParamVersionFeatures:
    """Test V004 generic parameter version checks."""

    @pytest.fixture
    def rule(self) -> GenericParamVersionFeatures:
        return GenericParamVersionFeatures()

    def test_type_var_allowed_on_38(self, rule: GenericParamVersionFeatures) -> None:
        """TypeVar is allowed on Python 3.8+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.8",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [{"name": "T", "kind": "type_var"}],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0

    def test_param_spec_requires_310(self, rule: GenericParamVersionFeatures) -> None:
        """ParamSpec requires Python 3.10+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.9",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [{"name": "P", "kind": "param_spec"}],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "V004" in issues[0].rule
        assert "param_spec" in issues[0].message
        assert "3.10" in issues[0].message

    def test_param_spec_allowed_on_310(self, rule: GenericParamVersionFeatures) -> None:
        """ParamSpec is allowed on Python 3.10+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [{"name": "P", "kind": "param_spec"}],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0

    def test_type_var_tuple_requires_311(
        self, rule: GenericParamVersionFeatures
    ) -> None:
        """TypeVarTuple requires Python 3.11+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [{"name": "Ts", "kind": "type_var_tuple"}],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "type_var_tuple" in issues[0].message
        assert "3.11" in issues[0].message

    def test_generic_default_requires_313(
        self, rule: GenericParamVersionFeatures
    ) -> None:
        """Generic parameter default (PEP 696) requires Python 3.13+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.12",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [
                            {"name": "T", "kind": "type_var", "default": "str"}
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "default" in issues[0].message.lower()
        assert "PEP 696" in issues[0].message
        assert "3.13" in issues[0].message

    def test_generic_default_allowed_on_313(
        self, rule: GenericParamVersionFeatures
    ) -> None:
        """Generic parameter default is allowed on Python 3.13+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.13",
                "types": [
                    {
                        "name": "MyGeneric",
                        "kind": "class",
                        "module": "testlib",
                        "generic_params": [
                            {"name": "T", "kind": "type_var", "default": "str"}
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0

    def test_functions_generic_params_checked(
        self, rule: GenericParamVersionFeatures
    ) -> None:
        """Generic params on functions are also checked."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.9",
                "functions": [
                    {
                        "name": "my_func",
                        "module": "testlib",
                        "signature": "() -> None",
                        "generic_params": [{"name": "P", "kind": "param_spec"}],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "param_spec" in issues[0].message


class TestExceptionGroupVersionFeatures:
    """Test V005 exception group version checks."""

    @pytest.fixture
    def rule(self) -> ExceptionGroupVersionFeatures:
        return ExceptionGroupVersionFeatures()

    def test_exception_group_in_method_raises(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """ExceptionGroup in method raises requires Python 3.11+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "testlib",
                        "methods": [
                            {
                                "name": "process",
                                "signature": "(self) -> None",
                                "description": "Process items",
                                "raises": [
                                    {"type": "ExceptionGroup", "description": "errors"}
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "V005" in issues[0].rule
        assert "ExceptionGroup" in issues[0].message
        assert "3.11" in issues[0].message

    def test_base_exception_group_also_checked(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """BaseExceptionGroup is also checked."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "testlib",
                        "methods": [
                            {
                                "name": "process",
                                "signature": "(self) -> None",
                                "description": "Process items",
                                "raises": [
                                    {
                                        "type": "BaseExceptionGroup",
                                        "description": "errors",
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "BaseExceptionGroup" in issues[0].message

    def test_exception_group_allowed_on_311(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """ExceptionGroup is allowed on Python 3.11+."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.11",
                "types": [
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "testlib",
                        "methods": [
                            {
                                "name": "process",
                                "signature": "(self) -> None",
                                "description": "Process items",
                                "raises": [
                                    {"type": "ExceptionGroup", "description": "errors"}
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0

    def test_exception_group_in_function_raises(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """ExceptionGroup in function raises is checked."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "functions": [
                    {
                        "name": "process_all",
                        "module": "testlib",
                        "signature": "() -> None",
                        "raises": [
                            {"type": "ExceptionGroup", "description": "errors"}
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "function" in issues[0].message.lower()

    def test_exception_group_in_constructor_raises(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """ExceptionGroup in constructor raises is checked."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "testlib",
                        "construction": {
                            "pattern": "init",
                            "raises": [
                                {"type": "ExceptionGroup", "description": "errors"}
                            ],
                        },
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "Constructor" in issues[0].message

    def test_exception_group_in_class_method_raises(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """ExceptionGroup in class method raises is checked."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.10",
                "types": [
                    {
                        "name": "MyClass",
                        "kind": "class",
                        "module": "testlib",
                        "class_methods": [
                            {
                                "name": "from_items",
                                "signature": "(cls) -> Self",
                                "description": "Factory method",
                                "raises": [
                                    {"type": "ExceptionGroup", "description": "errors"}
                                ],
                            }
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 1
        assert "class method" in issues[0].message.lower()

    def test_no_issues_without_python_requires(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """No issues raised if python_requires is not set."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                # no python_requires
                "functions": [
                    {
                        "name": "process_all",
                        "module": "testlib",
                        "signature": "() -> None",
                        "raises": [
                            {"type": "ExceptionGroup", "description": "errors"}
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0

    def test_regular_exceptions_not_flagged(
        self, rule: ExceptionGroupVersionFeatures
    ) -> None:
        """Regular exceptions are not flagged."""
        spec = {
            "library": {
                "name": "testlib",
                "version": "1.0.0",
                "python_requires": ">=3.8",
                "functions": [
                    {
                        "name": "process",
                        "module": "testlib",
                        "signature": "() -> None",
                        "raises": [
                            {"type": "ValueError", "description": "errors"},
                            {"type": "RuntimeError", "description": "errors"},
                        ],
                    }
                ],
            }
        }
        issues = list(rule.check(spec, {}))
        assert len(issues) == 0
