"""jq subprocess handling."""

import json
import shutil
import subprocess
from typing import Any


class JqNotFoundError(Exception):
    """jq is not installed or not in PATH."""

    pass


class JqError(Exception):
    """Error executing jq."""

    pass


def check_jq_available() -> bool:
    """Check if jq is available in PATH."""
    return shutil.which("jq") is not None


def run_jq(
    data: dict[str, Any],
    expression: str,
    raw: bool = False,
    compact: bool = False,
) -> str:
    """
    Run a jq expression on data.

    Args:
        data: The data to query
        expression: jq filter expression
        raw: Output raw strings without JSON encoding (-r)
        compact: Compact output (-c)

    Returns:
        The jq output as a string

    Raises:
        JqNotFoundError: If jq is not installed
        JqError: If jq fails to execute
    """
    if not check_jq_available():
        raise JqNotFoundError(
            "jq is required for query commands. "
            "Install it from https://jqlang.github.io/jq/download/"
        )

    cmd = ["jq"]
    if raw:
        cmd.append("-r")
    if compact:
        cmd.append("-c")
    cmd.append(expression)

    try:
        result = subprocess.run(
            cmd,
            input=json.dumps(data),
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise JqError("jq query timed out after 30 seconds")
    except OSError as e:
        raise JqError(f"Failed to run jq: {e}")

    if result.returncode != 0:
        raise JqError(f"jq error: {result.stderr.strip()}")

    return result.stdout


# Common query shortcuts
SHORTCUTS: dict[str, str] = {
    "type-names": ".library.types[].name",
    "function-names": ".library.functions[].name",
    "feature-ids": ".library.features[].id",
    "modules": ".library.modules[].path",
    "extensions": ".extensions",
    "version": ".library.version",
    "name": ".library.name",
}


def resolve_shortcut(query: str) -> str:
    """Resolve a shortcut to its jq expression, or return as-is."""
    return SHORTCUTS.get(query, query)
