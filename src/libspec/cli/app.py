"""Click application definition."""

from pathlib import Path

import click

from libspec.cli.config import LibspecConfig, find_spec_file
from libspec.cli.spec_loader import LoadedSpec, SpecLoadError, load_spec


class Context:
    """CLI context object passed to all commands."""

    def __init__(
        self,
        spec_path: str | None,
        text: bool,
        no_meta: bool,
        config: LibspecConfig,
        strict_models: bool,
    ):
        self.spec_path = spec_path
        self.text = text
        self.no_meta = no_meta
        self.config = config
        self.strict_models = strict_models
        self._spec: LoadedSpec | None = None

    def get_spec(self) -> LoadedSpec:
        """Get the loaded spec, loading it if needed."""
        if self._spec is None:
            path = find_spec_file(self.spec_path, self.config)
            if path is None:
                raise click.ClickException(
                    "No spec file found. Use --spec or set spec_path in [tool.libspec]"
                )
            try:
                self._spec = load_spec(path, strict=self.strict_models)
            except SpecLoadError as e:
                raise click.ClickException(str(e))
        return self._spec


pass_context = click.make_pass_decorator(Context)


@click.group()
@click.option(
    "--spec",
    "-s",
    type=click.Path(exists=False),
    help="Path to libspec.json (auto-detected if not specified)",
)
@click.option(
    "--text",
    "-t",
    is_flag=True,
    help="Token-minimal text output (default: JSON)",
)
@click.option(
    "--no-meta",
    is_flag=True,
    help="Omit metadata envelope from JSON output",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to pyproject.toml for [tool.libspec] config",
)
@click.option(
    "--strict-models/--no-strict-models",
    default=None,
    help="Enable strict Pydantic parsing (no coercion, extra fields rejected when extensions absent)",
)
@click.version_option(version="0.1.0", prog_name="libspec")
@click.pass_context
def cli(
    ctx: click.Context,
    spec: str | None,
    text: bool,
    no_meta: bool,
    config: str | None,
    strict_models: bool | None,
) -> None:
    """
    libspec - Query and analyze library specifications.

    All commands output JSON by default, designed for piping to jq.
    Use --text for compact, token-efficient output.

    \b
    Examples:
        libspec info                    # Overview of your spec
        libspec types --kind protocol   # List all protocols
        libspec query '.library.types[] | select(.kind=="class")'
        libspec lint --strict           # Lint and fail on issues
    """
    cfg = LibspecConfig.load(Path(config) if config else None)
    effective_strict = cfg.strict_models if strict_models is None else strict_models
    ctx.obj = Context(
        spec_path=spec,
        text=text,
        no_meta=no_meta,
        config=cfg,
        strict_models=effective_strict,
    )


# Import and register command groups (must be after cli definition to avoid circular imports)
from libspec.cli.commands import analyze, inspect, lifecycle, query, validate  # noqa: E402

cli.add_command(inspect.info)
cli.add_command(inspect.types)
cli.add_command(inspect.functions)
cli.add_command(inspect.features)
cli.add_command(inspect.modules)
cli.add_command(inspect.principles)

cli.add_command(query.query)
cli.add_command(query.refs)
cli.add_command(query.search)

cli.add_command(validate.validate)
cli.add_command(validate.lint)

cli.add_command(analyze.coverage)
cli.add_command(analyze.deps)
cli.add_command(analyze.surface)

cli.add_command(lifecycle.lifecycle)
