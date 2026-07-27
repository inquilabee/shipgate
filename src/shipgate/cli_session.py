"""CLI session: project root, ShipGateApp dispatch, and exit handling."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import typer

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.errors import ShipGateError
from shipgate.paths import find_project_root
from shipgate.runtime.project_python import persist_project_python

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class CliRunOptions:
    config: Path | None = None
    suite: str | None = None
    check: str | None = None
    target: Path | None = None
    error_format: str | None = None
    extra_arg: list[str] | None = None
    verbose: bool = False
    quiet: bool = False
    display_cli: bool = False
    ci: bool = False
    no_cache: bool = False
    changed_only: bool = False
    since: str | None = None
    project_env: Path | None = None


class CliSession:
    """Lifecycle owner for one CLI invocation against ShipGateApp."""

    def __init__(self, app: ShipGateApp | None = None) -> None:
        self.app = app or ShipGateApp()

    @staticmethod
    def build_run_command(project_root: Path, opts: CliRunOptions) -> RunCommand:
        return RunCommand(
            project_root=project_root,
            config_path=opts.config,
            suite=opts.suite,
            check=opts.check,
            target=opts.target,
            error_format=opts.error_format,
            extra_args=tuple(opts.extra_arg or []),
            verbose=opts.verbose,
            quiet=opts.quiet,
            display_cli=opts.display_cli,
            ci=opts.ci,
            no_cache=opts.no_cache,
            changed_only=opts.changed_only,
            since=opts.since,
        )

    @staticmethod
    def exit_code_from(exc: BaseException) -> int:
        code = getattr(exc, "exit_code", None)
        if isinstance(code, int):
            return code
        code = getattr(exc, "code", None)
        if isinstance(code, int):
            return code
        return 1

    @staticmethod
    def write_error(exc: ShipGateError) -> None:
        sys.stderr.write(exc.format() + "\n")

    @staticmethod
    def persist_project_env(project_root: Path, project_env: Path | None) -> None:
        if project_env is not None:
            persist_project_python(project_root, project_env)

    @staticmethod
    def project_root() -> Path:
        return find_project_root()

    @staticmethod
    def write_text(text: str) -> None:
        sys.stdout.write(text)
        raise typer.Exit(0)

    def install(
        self,
        *,
        config: Path | None,
        suite: str | None,
        project_env: Path | None,
        verbose: bool,
    ) -> None:
        self.install_like(
            update=False,
            config=config,
            suite=suite,
            project_env=project_env,
            verbose=verbose,
        )

    def update(
        self,
        *,
        config: Path | None,
        suite: str | None,
        project_env: Path | None,
        verbose: bool,
    ) -> None:
        self.install_like(
            update=True,
            config=config,
            suite=suite,
            project_env=project_env,
            verbose=verbose,
        )

    def run(self, mode: str, opts: CliRunOptions) -> None:
        project_root = self.project_root()
        self.persist_project_env(project_root, opts.project_env)
        command = self.build_run_command(project_root, opts)
        try:
            code = self.dispatch_run(mode, command)
        except ShipGateError as exc:
            self.write_error(exc)
            if opts.verbose:
                raise
            raise typer.Exit(exc.exit_code) from None
        except Exception as exc:
            # Catch-all mirrors legacy argparse CLI internal-error reporting.
            sys.stderr.write(f"shipgate: internal error: {exc}\n")
            if opts.verbose:
                raise
            raise typer.Exit(4) from None
        raise typer.Exit(code)

    def init(self, *, mode: str, configs_only: bool, project_env: Path | None) -> None:
        try:
            sys.stdout.write(
                self.app.init(
                    self.project_root(),
                    configs_only=configs_only,
                    mode=mode,
                    project_env=project_env,
                )
            )
        except ShipGateError as exc:
            self.write_error(exc)
            raise typer.Exit(exc.exit_code) from None
        raise typer.Exit(0)

    def configs_sync(self) -> None:
        self.write_text(self.app.configs_sync(self.project_root()))

    def configs_diff(self, tool: str | None) -> None:
        self.write_text(self.app.configs_diff(self.project_root(), tool))

    def configs_list(self, suite: str | None) -> None:
        self.write_text(self.app.configs_list(self.project_root(), suite=suite))

    def list_suites(self, *, verbose: bool, quiet: bool) -> None:
        if not quiet or verbose:
            sys.stdout.write(self.app.list_suites())
        raise typer.Exit(0)

    def list_tools(self, *, tag: str | None, verbose: bool, quiet: bool) -> None:
        if not quiet or verbose:
            sys.stdout.write(self.app.list_tools(tag=tag))
        raise typer.Exit(0)

    def list_checks(self, *, verbose: bool, quiet: bool) -> None:
        if not quiet or verbose:
            sys.stdout.write(self.app.list_checks(self.project_root()))
        raise typer.Exit(0)

    def schema(self) -> None:
        self.write_text(self.app.schema())

    def serve(self, *, host: str, port: int, open_browser: bool) -> None:
        code = self.app.serve(
            self.project_root(),
            host=host,
            port=port,
            open_browser=open_browser,
        )
        raise typer.Exit(code)

    def lock(self) -> None:
        raise typer.Exit(self.app.lock(self.project_root()))

    def baseline_show(self) -> None:
        self.write_text(self.app.baseline_show(self.project_root()))

    def batch(self, batch_file: Path) -> None:
        raise typer.Exit(self.app.run_batch(self.project_root(), batch_file))

    def gates_init(self, name: str) -> None:
        self.write_text(self.app.gates_init(self.project_root(), name))

    def gates_lib_path(self) -> None:
        self.write_text(self.app.gates_lib_path())

    def radon_calibrate(
        self,
        *,
        kind: str,
        paths: tuple[Path, ...] = (),
        json_path: Path | None = None,
        top: int = 15,
        yaml_snippet: bool = False,
    ) -> None:
        try:
            text = self.app.radon_calibrate(
                self.project_root(),
                kind=kind,
                paths=paths,
                json_path=json_path,
                top=top,
                yaml_snippet=yaml_snippet,
            )
        except ShipGateError as exc:
            self.write_error(exc)
            raise typer.Exit(exc.exit_code) from None
        self.write_text(text)

    def install_like(
        self,
        *,
        update: bool,
        config: Path | None,
        suite: str | None,
        project_env: Path | None,
        verbose: bool,
    ) -> None:
        project_root = self.project_root()
        self.persist_project_env(project_root, project_env)
        command = InstallCommand(project_root=project_root, config_path=config, suite=suite)
        try:
            code = self.app.update(command) if update else self.app.install(command)
        except ShipGateError as exc:
            self.write_error(exc)
            if verbose:
                raise
            raise typer.Exit(exc.exit_code) from None
        raise typer.Exit(code)

    def dispatch_run(self, mode: str, command: RunCommand) -> int:
        if mode == "format":
            return self.app.format(command)
        if mode == "baseline":
            return self.app.baseline_update(command)
        return self.app.check(command)
