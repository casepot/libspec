import json
from pathlib import Path

from click.testing import CliRunner

from libspec.cli import cli

FIXTURES = Path("docs/examples")


def run_cmd(args: list[str]):
    runner = CliRunner()
    result = runner.invoke(cli, args)
    assert result.exit_code == 0, result.output
    return result


def test_minimal_info_and_lint():
    spec = str(FIXTURES / "minimal.json")
    run_cmd(["--spec", spec, "--text", "info"])
    run_cmd(["--spec", spec, "--text", "types"])
    run_cmd(["--spec", spec, "lint"])


def test_lifecycle_info_and_lint_non_strict():
    spec = str(FIXTURES / "lifecycle.json")
    run_cmd(["--spec", spec, "--text", "info"])
    # default lint (non-strict) should pass even with informational issues
    run_cmd(["--spec", spec, "lint"])


def test_refs_accept_library_prefix():
    spec = str(FIXTURES / "minimal.json")
    result = run_cmd(["--spec", spec, "--text", "refs", "#/library/types/Greeter"])
    assert "Greeter" in result.output
