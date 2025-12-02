"""Regenerate Pydantic extension models from JSON Schemas.

- Runs datamodel-codegen for each extension schema
- Renames async.py -> async_.py to avoid keyword import issues
- Supports --check mode to fail if regenerated output differs from repo
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "src" / "libspec" / "schema" / "extensions"
OUTPUT_DIR = ROOT / "src" / "libspec" / "models" / "extensions"

CODEGEN_OPTS = [
    "--input-file-type",
    "jsonschema",
    "--output-model-type",
    "pydantic_v2.BaseModel",
    "--base-class",
    "libspec.models.base.ExtensionModel",
    "--use-standard-collections",
    "--use-union-operator",
    "--target-python-version",
    "3.10",
    "--disable-timestamp",
]


def datamodel_codegen_available() -> str:
    path = shutil.which("datamodel-codegen")
    if path is None:
        sys.stderr.write("datamodel-codegen is not installed. Install with `uv tool install datamodel-code-generator`.\n")
        sys.exit(1)
    return path


def generate_one(schema: Path, out_dir: Path, codegen_bin: str) -> None:
    out_path = out_dir / (schema.stem + ".py")
    cmd = [
        codegen_bin,
        "--input",
        str(schema),
        "--output",
        str(out_path),
        *CODEGEN_OPTS,
    ]
    subprocess.run(cmd, check=True, cwd=ROOT)


def rename_async(out_dir: Path) -> None:
    async_file = out_dir / "async.py"
    target = out_dir / "async_.py"
    if async_file.exists():
        if target.exists():
            target.unlink()
        async_file.rename(target)


def generate_all(out_dir: Path) -> None:
    codegen_bin = datamodel_codegen_available()
    out_dir.mkdir(parents=True, exist_ok=True)
    for schema in sorted(SCHEMA_DIR.glob("*.schema.json")):
        generate_one(schema, out_dir, codegen_bin)
    rename_async(out_dir)


def diff_dirs(a: Path, b: Path) -> bool:
    """Return True if dirs differ."""
    diff = subprocess.run(["git", "diff", "--no-index", str(a), str(b)])
    return diff.returncode != 0


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if check:
        with tempfile.TemporaryDirectory() as td:
            tmp_out = Path(td)
            generate_all(tmp_out)
            rename_async(tmp_out)
            if diff_dirs(tmp_out, OUTPUT_DIR):
                sys.stderr.write("Generated extension models are out of date. Run `uv run python tools/generate_models.py` to update.\n")
                return 1
        return 0

    generate_all(OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
