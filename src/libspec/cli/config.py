"""Configuration loading from pyproject.toml."""

import sys
from pathlib import Path

from pydantic import BaseModel, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[import-not-found]


class LintRuleConfig(BaseModel):
    """Configuration for a single lint rule."""

    severity: str | None = None
    enabled: bool = True


class LintConfig(BaseModel):
    """Lint configuration."""

    enable: list[str] = Field(default_factory=lambda: ["all"])
    disable: list[str] = Field(default_factory=list)
    rules: dict[str, str | LintRuleConfig] = Field(default_factory=dict)
    baseline_python_version: str = Field(
        default="3.8",
        description="Baseline Python version for V003 rule (features don't warn)",
    )

    def get_rule_severity(self, rule_id: str, default: str) -> str:
        """Get the configured severity for a rule."""
        rule_config = self.rules.get(rule_id)
        if rule_config is None:
            return default
        if isinstance(rule_config, str):
            return rule_config
        return rule_config.severity or default

    def is_rule_enabled(self, rule_id: str, category: str) -> bool:
        """Check if a rule is enabled."""
        # Check explicit disable
        if rule_id in self.disable or category in self.disable:
            return False

        # Check per-rule config
        rule_config = self.rules.get(rule_id)
        if isinstance(rule_config, LintRuleConfig) and not rule_config.enabled:
            return False

        # Check enable list
        if "all" in self.enable:
            return True
        return rule_id in self.enable or category in self.enable


class LibspecConfig(BaseModel):
    """Root configuration for libspec CLI."""

    spec_path: str = "specs/libspec.json"
    lint: LintConfig = Field(default_factory=LintConfig)
    strict_models: bool = False

    @classmethod
    def load(cls, config_path: Path | None = None) -> "LibspecConfig":
        """Load configuration from pyproject.toml."""
        if config_path is None:
            config_path = find_pyproject()

        if config_path is None or not config_path.exists():
            return cls()

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        tool_config = data.get("tool", {}).get("libspec", {})
        return cls.model_validate(tool_config)


def find_pyproject() -> Path | None:
    """Find pyproject.toml by walking up from cwd."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            return pyproject
    return None


def find_spec_file(spec_path: str | None, config: LibspecConfig) -> Path | None:
    """
    Find the spec file to use.

    Priority:
    1. Explicit --spec argument
    2. Config file spec_path
    3. Common locations: libspec.json, specs/libspec.json
    """
    if spec_path:
        path = Path(spec_path)
        if path.exists():
            return path
        return None

    # Try config path
    config_spec = Path(config.spec_path)
    if config_spec.exists():
        return config_spec

    # Try common locations
    common_paths = [
        Path("libspec.json"),
        Path("specs/libspec.json"),
        Path("spec/libspec.json"),
    ]
    for path in common_paths:
        if path.exists():
            return path

    return None
