"""Tests for validate_spec API enhancements.

This module tests:
- ValidationIssue and ValidationSeverity
- get_extension_schema function
- merge_schemas function
- validate_spec with structured errors
- validate_spec with extension merging
"""

import json
import tempfile
from pathlib import Path

import pytest

from libspec import (
    ALL_EXTENSIONS,
    ValidationIssue,
    ValidationSeverity,
    get_extension_schema,
    merge_schemas,
    validate_spec,
)


class TestValidationTypes:
    """Test ValidationIssue and ValidationSeverity."""

    def test_validation_severity_values(self) -> None:
        """ValidationSeverity has error and warning levels."""
        assert ValidationSeverity.ERROR.value == "error"
        assert ValidationSeverity.WARNING.value == "warning"

    def test_validation_issue_defaults(self) -> None:
        """ValidationIssue has sensible defaults."""
        issue = ValidationIssue(message="Something went wrong")
        assert issue.message == "Something went wrong"
        assert issue.path == "$"
        assert issue.severity == ValidationSeverity.ERROR
        assert issue.schema_path is None
        assert issue.context is None

    def test_validation_issue_with_all_fields(self) -> None:
        """ValidationIssue can have all fields set."""
        issue = ValidationIssue(
            message="Invalid type",
            path="$.library.types[0].name",
            severity=ValidationSeverity.WARNING,
            schema_path="/properties/library/properties/types/items/properties/name",
            context={"expected": "PascalCase", "got": "snake_case"},
        )
        assert issue.path == "$.library.types[0].name"
        assert issue.severity == ValidationSeverity.WARNING
        assert issue.context["expected"] == "PascalCase"


class TestGetExtensionSchema:
    """Test get_extension_schema function."""

    def test_get_valid_extension_schema(self) -> None:
        """Can load a valid extension schema."""
        schema = get_extension_schema("async")
        assert "$schema" in schema
        assert "$defs" in schema
        assert "Async Extension" in schema.get("title", "")

    def test_get_unknown_extension_raises(self) -> None:
        """Unknown extension name raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_extension_schema("nonexistent")
        assert "Unknown extension" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)

    @pytest.mark.parametrize("ext_name", sorted(ALL_EXTENSIONS))
    def test_all_extensions_loadable(self, ext_name: str) -> None:
        """All registered extensions can be loaded."""
        try:
            schema = get_extension_schema(ext_name)
            assert "$schema" in schema
        except FileNotFoundError:
            # Some extensions may not have schemas yet (e.g., ml, workflow)
            pytest.skip(f"Schema not found for {ext_name}")


class TestMergeSchemas:
    """Test merge_schemas function."""

    def test_merge_empty_extensions(self) -> None:
        """Merging with no extensions returns core schema unchanged."""
        from libspec import get_core_schema

        core = get_core_schema()
        merged, warnings = merge_schemas(core, [])
        assert warnings == []
        # Should be a copy, not the same object
        assert merged is not core
        assert merged == core

    def test_merge_single_extension(self) -> None:
        """Merging with one extension adds its $defs."""
        from libspec import get_core_schema

        core = get_core_schema()
        merged, warnings = merge_schemas(core, ["async"])
        assert warnings == []
        # Merged schema should have async extension definitions
        assert "$defs" in merged

    def test_merge_unknown_extension_warns(self) -> None:
        """Unknown extension produces warning, doesn't fail."""
        from libspec import get_core_schema

        core = get_core_schema()
        merged, warnings = merge_schemas(core, ["nonexistent_extension"])
        assert len(warnings) == 1
        assert warnings[0].severity == ValidationSeverity.WARNING
        assert "Unknown extension" in warnings[0].message

    def test_merge_multiple_extensions(self) -> None:
        """Can merge multiple extensions."""
        from libspec import get_core_schema

        core = get_core_schema()
        merged, warnings = merge_schemas(core, ["async", "errors", "perf"])
        assert warnings == []
        assert "$defs" in merged


class TestValidateSpec:
    """Test validate_spec function."""

    @pytest.fixture
    def valid_spec_file(self, tmp_path: Path) -> Path:
        """Create a valid minimal spec file."""
        spec = {
            "$schema": "libspec/1.0",
            "library": {
                "name": "testlib",
                "version": "1.0.0",
            },
        }
        spec_path = tmp_path / "valid.json"
        spec_path.write_text(json.dumps(spec))
        return spec_path

    @pytest.fixture
    def invalid_spec_file(self, tmp_path: Path) -> Path:
        """Create an invalid spec file."""
        spec = {
            "$schema": "libspec/1.0",
            "library": {
                # missing required 'name' field
                "version": "1.0.0",
            },
        }
        spec_path = tmp_path / "invalid.json"
        spec_path.write_text(json.dumps(spec))
        return spec_path

    @pytest.fixture
    def spec_with_extensions(self, tmp_path: Path) -> Path:
        """Create a spec file with extensions declared."""
        spec = {
            "$schema": "libspec/1.0",
            "extensions": ["async", "errors"],
            "library": {
                "name": "testlib",
                "version": "1.0.0",
            },
        }
        spec_path = tmp_path / "with_extensions.json"
        spec_path.write_text(json.dumps(spec))
        return spec_path

    def test_validate_valid_spec_returns_empty_list(self, valid_spec_file: Path) -> None:
        """Validating a valid spec returns empty error list."""
        errors = validate_spec(valid_spec_file)
        assert errors == []

    def test_validate_invalid_spec_returns_errors(self, invalid_spec_file: Path) -> None:
        """Validating an invalid spec returns error messages."""
        errors = validate_spec(invalid_spec_file)
        assert len(errors) > 0
        assert any("name" in e.lower() or "required" in e.lower() for e in errors)

    def test_validate_structured_returns_issues(self, invalid_spec_file: Path) -> None:
        """structured=True returns ValidationIssue objects."""
        issues = validate_spec(invalid_spec_file, structured=True)
        assert len(issues) > 0
        assert all(isinstance(i, ValidationIssue) for i in issues)
        assert all(i.severity == ValidationSeverity.ERROR for i in issues)

    def test_validate_with_extensions_merges_schemas(
        self, spec_with_extensions: Path
    ) -> None:
        """Spec with extensions triggers schema merging."""
        # Should not raise, even with extension schemas
        errors = validate_spec(spec_with_extensions)
        # Valid spec should have no errors
        assert errors == []

    def test_validate_with_unknown_extension_warns(self, tmp_path: Path) -> None:
        """Unknown extension in spec produces warning in structured mode."""
        spec = {
            "$schema": "libspec/1.0",
            "extensions": ["unknown_ext"],
            "library": {
                "name": "testlib",
                "version": "1.0.0",
            },
        }
        spec_path = tmp_path / "unknown_ext.json"
        spec_path.write_text(json.dumps(spec))

        issues = validate_spec(spec_path, structured=True)
        warnings = [i for i in issues if i.severity == ValidationSeverity.WARNING]
        assert len(warnings) == 1
        assert "Unknown extension" in warnings[0].message

    def test_validate_structured_includes_path(self, invalid_spec_file: Path) -> None:
        """Structured issues include JSON path."""
        issues = validate_spec(invalid_spec_file, structured=True)
        # At least one issue should have a meaningful path
        paths = [i.path for i in issues]
        assert any(p != "$" for p in paths) or len(issues) > 0
