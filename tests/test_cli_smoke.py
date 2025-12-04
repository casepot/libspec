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


def test_workflow_info_and_lint_non_strict():
    spec = str(FIXTURES / "workflow.json")
    run_cmd(["--spec", spec, "--text", "info"])
    # default lint (non-strict) should pass even with informational issues
    run_cmd(["--spec", spec, "lint"])


def test_refs_accept_library_prefix():
    spec = str(FIXTURES / "minimal.json")
    result = run_cmd(["--spec", spec, "--text", "refs", "#/library/types/Greeter"])
    assert "Greeter" in result.output


def test_refs_nested_method():
    """Test that nested method refs like #/types/Request/methods/with_headers resolve correctly."""
    spec = str(FIXTURES / "http-client.json")
    result = run_cmd(["--spec", spec, "refs", "#/types/Request/methods/with_headers"])
    data = json.loads(result.output)
    assert data["result"]["resolved"]["name"] == "with_headers"
    assert "signature" in data["result"]["resolved"]


def test_refs_nested_method_text():
    """Test nested method refs in text mode."""
    spec = str(FIXTURES / "http-client.json")
    result = run_cmd(["--spec", spec, "--text", "refs", "#/types/Request/methods/with_headers"])
    assert "with_headers" in result.output
