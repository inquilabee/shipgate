"""ShipGate CLI (Typer)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated

import typer

from shipgate.cli_session import CliRunOptions, CliSession
from shipgate.errors import ShipGateError

TOP_LEVEL_COMMANDS = frozenset(
    {
        "install",
        "update",
        "init",
        "configs",
        "format",
        "check",
        "list",
        "schema",
        "serve",
        "lock",
        "baseline",
        "batch",
        "gates",
        "radon",
        "refactor",
    }
)

CONFIGS_ONLY_HELP = "Scaffold .shipgate/configs without creating policy"

app = typer.Typer(
    name="shipgate",
    help="Quality gate orchestrator",
    no_args_is_help=False,
    add_completion=False,
)
init_app = typer.Typer(help="Scaffold ShipGate project policy and layout", no_args_is_help=False)
configs_app = typer.Typer(help="Project tool config management")
list_app = typer.Typer(help="List catalog metadata")
baseline_app = typer.Typer(help="Baseline management")
gates_app = typer.Typer(help="Local gates")
radon_app = typer.Typer(help="Radon metric helpers")

app.add_typer(init_app, name="init")
app.add_typer(configs_app, name="configs")
app.add_typer(list_app, name="list")
app.add_typer(baseline_app, name="baseline")
app.add_typer(gates_app, name="gates")
app.add_typer(radon_app, name="radon")

ConfigOpt = Annotated[Path | None, typer.Option("--config", help="Path to shipgate.yaml")]
SuiteOpt = Annotated[str | None, typer.Option("--suite", help="Suite to run")]
CheckOpt = Annotated[str | None, typer.Option("--check", help="Single check to run")]
TargetOpt = Annotated[Path | None, typer.Option("--target", help="Target path")]
ErrorFormatOpt = Annotated[str | None, typer.Option("--error-format", help="Error output format")]
ExtraArgOpt = Annotated[list[str] | None, typer.Option("--extra-arg", help="Extra tool argument")]
VerboseOpt = Annotated[bool, typer.Option("--verbose", help="Verbose output")]
QuietOpt = Annotated[bool, typer.Option("--quiet", help="Quiet success")]
DisplayCliOpt = Annotated[
    bool,
    typer.Option(
        "--display-cli",
        help="Print each tool subprocess command to stderr before execution",
    ),
]
CiOpt = Annotated[bool, typer.Option("--ci", help="CI mode")]
NoCacheOpt = Annotated[bool, typer.Option("--no-cache", help="Disable check result cache")]
ChangedOnlyOpt = Annotated[bool, typer.Option("--changed-only", help="Incremental checks")]
FullTreeOpt = Annotated[
    bool,
    typer.Option(
        "--full-tree",
        help="Scan the whole tree; ignore changed-only and --since for this run",
    ),
]
SinceOpt = Annotated[str | None, typer.Option("--since", help="Git ref for incremental checks")]
ProjectEnvOpt = Annotated[
    Path | None,
    typer.Option(
        "--project-env",
        help="Project Python environment path; saved to .shipgate/cache/.env",
    ),
]
ConfigsOnlyOpt = Annotated[bool, typer.Option("--configs-only", help=CONFIGS_ONLY_HELP)]


def normalize_argv(argv: list[str] | None) -> list[str]:
    if argv is None:
        argv = sys.argv[1:]
    return (
        (
            ["check", *argv]
            if not argv[0].startswith("-") and argv[0] not in TOP_LEVEL_COMMANDS
            else list(argv)
        )
        if argv
        else ["check"]
    )


def session() -> CliSession:
    return CliSession()


def register_run_command(typer_app: typer.Typer, name: str, *, mode: str) -> None:
    def command(
        *,
        config: ConfigOpt = None,
        suite: SuiteOpt = None,
        check: CheckOpt = None,
        target: TargetOpt = None,
        error_format: ErrorFormatOpt = None,
        extra_arg: ExtraArgOpt = None,
        verbose: VerboseOpt = False,
        quiet: QuietOpt = False,
        display_cli: DisplayCliOpt = False,
        ci: CiOpt = False,
        no_cache: NoCacheOpt = False,
        changed_only: ChangedOnlyOpt = False,
        full_tree: FullTreeOpt = False,
        since: SinceOpt = None,
        project_env: ProjectEnvOpt = None,
    ) -> None:
        session().run(
            mode,
            CliRunOptions(
                config=config,
                suite=suite,
                check=check,
                target=target,
                error_format=error_format,
                extra_arg=extra_arg,
                verbose=verbose,
                quiet=quiet,
                display_cli=display_cli,
                ci=ci,
                no_cache=no_cache,
                changed_only=changed_only,
                full_tree=full_tree,
                since=since,
                project_env=project_env,
            ),
        )

    command.__name__ = f"{name}_cmd"
    command.__qualname__ = f"{name}_cmd"
    typer_app.command(name)(command)


@app.command("install")
def install_cmd(
    *,
    config: ConfigOpt = None,
    suite: SuiteOpt = None,
    project_env: ProjectEnvOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    session().install(
        config=config,
        suite=suite,
        project_env=project_env,
        verbose=verbose,
    )


@app.command("update")
def update_cmd(
    *,
    config: ConfigOpt = None,
    suite: SuiteOpt = None,
    project_env: ProjectEnvOpt = None,
    verbose: VerboseOpt = False,
) -> None:
    session().update(
        config=config,
        suite=suite,
        project_env=project_env,
        verbose=verbose,
    )


register_run_command(app, "format", mode="format")
register_run_command(app, "check", mode="check")
register_run_command(baseline_app, "update", mode="baseline")


@init_app.callback(invoke_without_command=True)
def init_root(
    ctx: typer.Context,
    *,
    configs_only: ConfigsOnlyOpt = False,
    project_env: ProjectEnvOpt = None,
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    session().init(mode="yaml", configs_only=configs_only, project_env=project_env)


@init_app.command("yaml")
def init_yaml(
    *,
    configs_only: ConfigsOnlyOpt = False,
    project_env: ProjectEnvOpt = None,
) -> None:
    session().init(mode="yaml", configs_only=configs_only, project_env=project_env)


@init_app.command("pyproject")
def init_pyproject(
    *,
    configs_only: ConfigsOnlyOpt = False,
    project_env: ProjectEnvOpt = None,
) -> None:
    session().init(mode="pyproject", configs_only=configs_only, project_env=project_env)


@configs_app.command("sync")
def configs_sync() -> None:
    session().configs_sync()


@configs_app.command("diff")
def configs_diff(tool: Annotated[str | None, typer.Argument()] = None) -> None:
    session().configs_diff(tool)


@configs_app.command("list")
def configs_list(*, suite: SuiteOpt = None) -> None:
    session().configs_list(suite)


@list_app.command("suites")
def list_suites(*, verbose: VerboseOpt = False, quiet: QuietOpt = False) -> None:
    session().list_suites(verbose=verbose, quiet=quiet)


@list_app.command("tools")
def list_tools(
    *,
    tag: Annotated[str | None, typer.Option("--tag", help="Filter tools by catalog tag")] = None,
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    session().list_tools(tag=tag, verbose=verbose, quiet=quiet)


@list_app.command("checks")
def list_checks(*, verbose: VerboseOpt = False, quiet: QuietOpt = False) -> None:
    session().list_checks(verbose=verbose, quiet=quiet)


@app.command("schema")
def schema_cmd() -> None:
    session().schema()


@app.command("serve")
def serve_cmd(
    *,
    host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
    port: Annotated[int, typer.Option("--port")] = 8765,
    open_browser: Annotated[bool, typer.Option("--open", help="Open browser")] = False,
) -> None:
    session().serve(host=host, port=port, open_browser=open_browser)


@app.command("lock")
def lock_cmd() -> None:
    session().lock()


@baseline_app.command("show")
def baseline_show() -> None:
    session().baseline_show()


@app.command("batch")
def batch_cmd(batch_file: Annotated[Path, typer.Argument()]) -> None:
    session().batch(batch_file)


@gates_app.command("init")
def gates_init(name: Annotated[str, typer.Argument()] = "gate") -> None:
    session().gates_init(name)


@gates_app.command("lib-path")
def gates_lib_path() -> None:
    session().gates_lib_path()


@radon_app.command("calibrate")
def radon_calibrate(
    kind: Annotated[str, typer.Argument(help="Metric kind: mi or cc")],
    *,
    path: Annotated[
        list[Path] | None,
        typer.Option("--path", help="Path for radon scan (repeatable; default .)"),
    ] = None,
    json_file: Annotated[
        Path | None,
        typer.Option("--json-file", help="Use existing radon JSON instead of running radon"),
    ] = None,
    top: Annotated[int, typer.Option("--top", help="Worst offenders to list")] = 15,
    yaml_snippet: Annotated[
        bool,
        typer.Option("--yaml", help="Print only the suggested YAML binding snippet"),
    ] = False,
) -> None:
    session().radon_calibrate(
        kind=kind,
        paths=tuple(path or []),
        json_path=json_file,
        top=top,
        yaml_snippet=yaml_snippet,
    )


@radon_app.command("reset")
def radon_reset() -> None:
    """Delete progressive radon baselines from .shipgate/cache/.env."""
    session().radon_reset()


@app.command(
    "refactor",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
    add_help_option=False,
)
def refactor_cmd(ctx: typer.Context) -> None:
    """AST refactor checks and autofixes (check / fix / list / explain)."""
    from refactor.cli import main as refactor_main

    raise typer.Exit(refactor_main(list(ctx.args), prog="shipgate refactor"))


def main(argv: list[str] | None = None) -> int:
    normalized = normalize_argv(argv)
    try:
        # standalone_mode=False: Click returns exit codes instead of sys.exit.
        result = app(args=normalized, standalone_mode=False)
    except SystemExit as exc:
        return CliSession.exit_code_from(exc)
    except typer.Exit as exc:
        return CliSession.exit_code_from(exc)
    except ShipGateError as exc:
        CliSession.write_error(exc)
        return exc.exit_code
    except Exception as exc:  # ruff: ignore[blind-except] — CLI catch-all exit path
        sys.stderr.write(f"shipgate: internal error: {exc}\n")
        return 4
    return result if isinstance(result, int) else 0


if __name__ == "__main__":
    raise SystemExit(main())
