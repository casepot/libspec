"""Testing extension models for libspec specifications.

This module defines models for testing-related specifications:
- Fixtures, markers, hooks (pytest integration)
- Mocks, stubs, fakes (test doubles)
- Factories (test data generation)
- Coverage configuration
- Common pytest plugins (pytest-asyncio, pytest-mock, pytest-cov)
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Any

from pydantic import Field

from libspec.models.base import ExtensionModel
from libspec.models.types import FunctionReference, LocalPath, NonEmptyStr, TypeAnnotationStr

# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------


class FixtureScope(str, Enum):
    """Pytest fixture scope."""

    function = "function"
    class_ = "class"
    module = "module"
    package = "package"
    session = "session"


class MockType(str, Enum):
    """Type of test double."""

    mock = "mock"
    stub = "stub"
    spy = "spy"
    fake = "fake"
    dummy = "dummy"


class TestCategory(str, Enum):
    """Test pattern category."""

    unit = "unit"
    integration = "integration"
    e2e = "e2e"
    property_ = "property"
    snapshot = "snapshot"
    contract = "contract"
    performance = "performance"


class CoverageTool(str, Enum):
    """Coverage measurement tool."""

    coverage_py = "coverage.py"
    pytest_cov = "pytest-cov"
    istanbul = "istanbul"
    jacoco = "jacoco"
    custom = "custom"


class ConftestScope(str, Enum):
    """Scope of a conftest.py file."""

    project = "project"
    package = "package"
    module = "module"


class HookPhase(str, Enum):
    """Pytest hook execution phase."""

    configure = "configure"
    collection = "collection"
    runtest = "runtest"
    reporting = "reporting"
    sessionstart = "sessionstart"
    sessionfinish = "sessionfinish"


class AsyncioMode(str, Enum):
    """pytest-asyncio mode setting."""

    auto = "auto"
    strict = "strict"


class CoverageReportFormat(str, Enum):
    """Coverage report output format."""

    term = "term"
    term_missing = "term-missing"
    html = "html"
    xml = "xml"
    json = "json"
    lcov = "lcov"


# -----------------------------------------------------------------------------
# Fixture and Test Double Models
# -----------------------------------------------------------------------------


class FixtureSpec(ExtensionModel):
    """A pytest fixture definition."""

    name: NonEmptyStr = Field(description="Fixture name")
    scope: FixtureScope | None = Field(default=None, description="Fixture scope")
    type: TypeAnnotationStr | None = Field(default=None, description="Return type annotation")
    factory: FunctionReference | None = Field(
        default=None, description="Factory function reference"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Other fixtures this depends on"
    )
    autouse: bool | None = Field(
        default=None, description="Whether fixture is automatically used"
    )
    params: list[Any] | None = Field(
        default=None, description="Parameterization values"
    )
    yields: bool | None = Field(
        default=None, description="Whether fixture uses yield (generator)"
    )
    async_: bool | None = Field(
        default=None, alias="async", description="Whether fixture is async"
    )
    cleanup: str | None = Field(
        default=None, description="Cleanup behavior description"
    )
    description: str | None = Field(default=None, description="What this fixture provides")


class MockSpec(ExtensionModel):
    """A mock/stub utility definition."""

    name: NonEmptyStr = Field(description="Mock utility name")
    type: MockType | None = Field(default=None, description="Type of test double")
    target: str | None = Field(
        default=None, description="What this mocks (type reference)"
    )
    factory: FunctionReference | None = Field(
        default=None, description="Factory function reference"
    )
    configurable: list[str] = Field(
        default_factory=list, description="Configurable behaviors"
    )
    auto_spec: bool | None = Field(
        default=None, description="Whether spec is auto-generated from target"
    )
    description: str | None = Field(default=None, description="What this mock provides")


class TestDoubleSpec(ExtensionModel):
    """Test double configuration for a type."""

    provided: bool | None = Field(
        default=None, description="Whether library provides a test double"
    )
    type: str | None = Field(default=None, description="Test double type reference")
    builder: FunctionReference | None = Field(default=None, description="Builder function reference")
    configurable_behaviors: list[str] = Field(
        default_factory=list, description="Behaviors that can be configured"
    )


# -----------------------------------------------------------------------------
# Factory Models (test data generation)
# -----------------------------------------------------------------------------


class FactoryFieldSpec(ExtensionModel):
    """A factory field definition."""

    name: NonEmptyStr = Field(description="Field name")
    default: Any | None = Field(default=None, description="Default value or generator")
    faker: str | None = Field(
        default=None, description="Faker provider (e.g., 'name', 'email')"
    )
    sequence: bool | None = Field(
        default=None, description="Whether this is a sequence"
    )
    lazy: bool | None = Field(
        default=None, description="Whether value is lazily evaluated"
    )
    subfactory: str | None = Field(default=None, description="Subfactory reference")


class TraitSpec(ExtensionModel):
    """A factory trait (named variation)."""

    name: NonEmptyStr = Field(description="Trait name")
    overrides: dict[str, Any] | None = Field(
        default=None, description="Field overrides"
    )
    description: str | None = Field(default=None, description="What this trait represents")


class SequenceSpec(ExtensionModel):
    """A sequence generator for factories."""

    name: NonEmptyStr = Field(description="Sequence name")
    pattern: str | None = Field(
        default=None, description="Pattern with {n} placeholder"
    )
    start: Annotated[int, Field(ge=1)] | None = Field(default=1, description="Starting value")


class FactorySpec(ExtensionModel):
    """A test data factory definition."""

    name: NonEmptyStr = Field(description="Factory name")
    model: str = Field(description="Model type this creates")
    fields: list[FactoryFieldSpec] = Field(
        default_factory=list, description="Field definitions"
    )
    traits: list[TraitSpec] = Field(
        default_factory=list, description="Named trait variations"
    )
    sequences: list[SequenceSpec] = Field(
        default_factory=list, description="Sequence generators"
    )
    subfactories: list[str] = Field(
        default_factory=list, description="Related subfactories"
    )
    lazy_attributes: list[str] = Field(
        default_factory=list, description="Lazily evaluated attributes"
    )
    description: str | None = Field(default=None, description="What this factory creates")


# -----------------------------------------------------------------------------
# Assertion and Pattern Models
# -----------------------------------------------------------------------------


class AssertionSpec(ExtensionModel):
    """A custom assertion definition."""

    name: NonEmptyStr = Field(description="Assertion name")
    signature: str | None = Field(default=None, description="Function signature")
    checks: str | None = Field(default=None, description="What this assertion checks")
    failure_message: str | None = Field(
        default=None, description="Message format on failure"
    )
    negated_name: str | None = Field(
        default=None, description="Name of negated version (if exists)"
    )
    description: str | None = Field(default=None, description="What this assertion verifies")


class TestPatternSpec(ExtensionModel):
    """A recommended test pattern."""

    name: NonEmptyStr = Field(description="Pattern name")
    category: TestCategory | None = Field(default=None, description="Pattern category")
    applies_to: list[str] = Field(
        default_factory=list, description="Types/features this pattern applies to"
    )
    setup: str | None = Field(default=None, description="Setup instructions")
    example: str | None = Field(default=None, description="Example test code")
    fixtures_used: list[str] = Field(
        default_factory=list, description="Fixtures typically used"
    )
    description: str | None = Field(default=None, description="When to use this pattern")


# -----------------------------------------------------------------------------
# Coverage Models
# -----------------------------------------------------------------------------


class CoverageTargetSpec(ExtensionModel):
    """A coverage target definition."""

    path: str | None = Field(default=None, description="Path or module")
    minimum: Annotated[float, Field(ge=0.0, le=100.0)] | None = Field(
        default=None, description="Minimum coverage percentage"
    )


class CoverageSpec(ExtensionModel):
    """Test coverage configuration."""

    tool: CoverageTool | None = Field(default=None, description="Coverage tool")
    targets: list[CoverageTargetSpec] = Field(
        default_factory=list, description="Coverage targets"
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="Patterns to exclude from coverage"
    )
    branch_coverage: bool | None = Field(
        default=None, description="Whether branch coverage is tracked"
    )


# -----------------------------------------------------------------------------
# Pytest Marker, Hook, and Conftest Models
# -----------------------------------------------------------------------------


class MarkerArgSpec(ExtensionModel):
    """A pytest marker argument specification."""

    name: NonEmptyStr = Field(description="Argument name")
    type: TypeAnnotationStr | None = Field(default=None, description="Argument type")
    required: bool = Field(default=False, description="Whether argument is required")
    description: str | None = Field(default=None, description="What this argument controls")


class MarkerSpec(ExtensionModel):
    """A custom pytest marker definition."""

    name: NonEmptyStr = Field(description="Marker name (e.g., 'slow', 'integration')")
    description: str | None = Field(default=None, description="What this marker indicates")
    args: list[MarkerArgSpec] = Field(
        default_factory=list, description="Arguments the marker accepts"
    )
    strict: bool | None = Field(
        default=None,
        description="Whether unknown markers should error (pytest --strict-markers)",
    )
    skip_reason: str | None = Field(
        default=None, description="For skip markers: the default skip reason"
    )
    xfail_reason: str | None = Field(
        default=None, description="For xfail markers: the expected failure reason"
    )


class ConftestSpec(ExtensionModel):
    """Documentation for a conftest.py file."""

    path: LocalPath = Field(description="Path to conftest.py relative to project root")
    scope: ConftestScope | None = Field(
        default=None, description="Scope of fixtures in this conftest"
    )
    fixtures_provided: list[str] = Field(
        default_factory=list, description="Fixtures defined in this conftest"
    )
    plugins_configured: list[str] = Field(
        default_factory=list, description="Pytest plugins configured here"
    )
    hooks_implemented: list[str] = Field(
        default_factory=list, description="Pytest hooks implemented here"
    )
    description: str | None = Field(default=None, description="Purpose of this conftest")


class HookSpec(ExtensionModel):
    """A pytest hook implementation."""

    name: NonEmptyStr = Field(
        description="Hook name (e.g., 'pytest_configure', 'pytest_collection_modifyitems')"
    )
    phase: HookPhase | None = Field(default=None, description="When this hook runs")
    purpose: str | None = Field(
        default=None, description="What this hook implementation does"
    )
    location: FunctionReference | None = Field(
        default=None, description="File where this hook is implemented"
    )
    tryfirst: bool | None = Field(
        default=None, description="Whether this hook runs before others"
    )
    trylast: bool | None = Field(
        default=None, description="Whether this hook runs after others"
    )
    hookwrapper: bool | None = Field(
        default=None, description="Whether this is a hook wrapper"
    )


class ParametrizeSpec(ExtensionModel):
    """A common parametrization pattern."""

    name: NonEmptyStr = Field(description="Pattern name for reference")
    params: list[str] = Field(description="Parameter names")
    values_source: str | None = Field(
        default=None, description="Where values come from (fixture, constant, file, etc.)"
    )
    indirect: list[str] = Field(
        default_factory=list,
        description="Parameters that should be passed through fixtures",
    )
    ids: str | None = Field(default=None, description="How test IDs are generated")
    example: str | None = Field(default=None, description="Example usage")
    description: str | None = Field(default=None, description="When to use this pattern")


# -----------------------------------------------------------------------------
# Pytest Plugin Configuration Models
# -----------------------------------------------------------------------------


class SpyPatternSpec(ExtensionModel):
    """A pytest-mock spy pattern."""

    target: str | None = Field(default=None, description="Target object/module")
    method: str | None = Field(default=None, description="Method to spy on")
    purpose: str | None = Field(default=None, description="Why this spy is used")


class PatchPatternSpec(ExtensionModel):
    """A pytest-mock patch pattern."""

    target: str | None = Field(default=None, description="Target to patch")
    return_value: str | None = Field(default=None, description="Mocked return value")
    purpose: str | None = Field(default=None, description="Why this patch is used")


class PytestAsyncioConfig(ExtensionModel):
    """pytest-asyncio plugin configuration."""

    mode: AsyncioMode | None = Field(default=None, description="Asyncio mode")
    default_fixture_loop_scope: FixtureScope | None = Field(
        default=None, description="Default scope for async fixtures"
    )
    event_loop_policy: str | None = Field(
        default=None, description="Custom event loop policy class"
    )
    async_fixtures: list[str] = Field(
        default_factory=list, description="Async fixture names in the project"
    )


class PytestMockConfig(ExtensionModel):
    """pytest-mock plugin configuration."""

    mocker_fixture: bool = Field(
        default=True, description="Whether MockerFixture is used"
    )
    spy_patterns: list[SpyPatternSpec] = Field(
        default_factory=list, description="Common spy usage patterns"
    )
    patch_patterns: list[PatchPatternSpec] = Field(
        default_factory=list, description="Common patch patterns"
    )


class PytestCovConfig(ExtensionModel):
    """pytest-cov plugin configuration."""

    source: list[str] = Field(
        default_factory=list, description="Source directories to measure"
    )
    omit: list[str] = Field(
        default_factory=list, description="Patterns to omit from coverage"
    )
    fail_under: Annotated[float, Field(ge=0.0, le=100.0)] | None = Field(
        default=None, description="Minimum coverage percentage to pass"
    )
    branch: bool | None = Field(
        default=None, description="Whether branch coverage is enabled"
    )
    report_formats: list[CoverageReportFormat] = Field(
        default_factory=list, description="Report formats to generate"
    )


class PytestPluginConfig(ExtensionModel):
    """Configuration for common pytest plugins."""

    pytest_asyncio: PytestAsyncioConfig | None = Field(
        default=None, description="pytest-asyncio configuration"
    )
    pytest_mock: PytestMockConfig | None = Field(
        default=None, description="pytest-mock configuration"
    )
    pytest_cov: PytestCovConfig | None = Field(
        default=None, description="pytest-cov configuration"
    )


# -----------------------------------------------------------------------------
# Extension Field Containers
# -----------------------------------------------------------------------------


class TestingTypeFields(ExtensionModel):
    """Fields added to TypeDef when testing extension is active."""

    testable: bool | None = Field(
        default=None, description="Whether type is designed for testing"
    )
    test_double: TestDoubleSpec | None = Field(
        default=None, description="Test double configuration"
    )
    golden_tests: list[str] = Field(
        default_factory=list, description="Golden test file references"
    )


class TestingLibraryFields(ExtensionModel):
    """Fields added to Library when testing extension is active."""

    fixtures: list[FixtureSpec] = Field(
        default_factory=list, description="Test fixture definitions"
    )
    markers: list[MarkerSpec] = Field(
        default_factory=list, description="Custom pytest markers"
    )
    conftest_files: list[ConftestSpec] = Field(
        default_factory=list, description="Conftest.py file documentation"
    )
    hooks: list[HookSpec] = Field(
        default_factory=list, description="Pytest hook implementations"
    )
    parametrize_patterns: list[ParametrizeSpec] = Field(
        default_factory=list, description="Common parametrization patterns"
    )
    mocks: list[MockSpec] = Field(
        default_factory=list, description="Mock/stub utilities"
    )
    factories: list[FactorySpec] = Field(
        default_factory=list, description="Test data factories"
    )
    assertions: list[AssertionSpec] = Field(
        default_factory=list, description="Custom assertions"
    )
    test_patterns: list[TestPatternSpec] = Field(
        default_factory=list, description="Recommended test patterns"
    )
    coverage: CoverageSpec | None = Field(
        default=None, description="Test coverage configuration"
    )
    pytest_plugins: PytestPluginConfig | None = Field(
        default=None, description="Configuration for common pytest plugins"
    )
