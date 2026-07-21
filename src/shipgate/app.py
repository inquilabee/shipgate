"""Application service layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from shipgate.adapter.argv import build_argv
from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.baseline import load_baseline, save_baseline
from shipgate.catalog.loader import load_catalog
from shipgate.config.loader import load_config
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import SCHEMA_VERSION, CheckReport, RunReport
from shipgate.formatters.plugins import get_formatter
from shipgate.gates.init import init_gate
from shipgate.normalize.base import get_normalizer
from shipgate.planning.requests import build_execution_request, resolve_request
from shipgate.planning.scopes import resolve_scope, scope_paths
from shipgate.planning.workflow import resolve_runnables
from shipgate.runtime.environment import resolve_environment, resolve_executable
from shipgate.runtime.executor import Executor, ProcessResult
from shipgate.runtime.install import install_suite
from shipgate.runtime.lockfile import write_lockfile
from shipgate.runtime.reports import generate_run_id, write_raw_output, write_run_report

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.project import ProjectConfig, Scope


@dataclass(frozen=True)
class RunCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None
    check: str | None = None
    target: Path | None = None
    error_format: str | None = None
    extra_args: tuple[str, ...] = ()
    verbose: bool = False
    quiet: bool = False
    ci: bool = False
    no_cache: bool = False
    changed_only: bool = False
    since: str | None = None


@dataclass(frozen=True)
class InstallCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None


@dataclass(frozen=True)
class RunProgress:
    current_check_id: str
    checks_completed: int
    checks_total: int


@dataclass(frozen=True)
class _RunContext:
    project: ProjectConfig
    project_root: Path
    suite_id: str
    tool_ids: tuple[str, ...]
    environment: object
    scope: Scope
    paths: tuple[Path, ...]


class ExecutorProtocol(Protocol):
    def run(
        self,
        argv: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> ProcessResult: ...


class ShipGateApp:
    def __init__(
        self,
        *,
        catalog: Catalog | None = None,
        executor: ExecutorProtocol | None = None,
    ) -> None:
        self.catalog = catalog or load_catalog()
        self._executor_is_default = executor is None
        self.executor = executor or Executor()

    def install(self, command: InstallCommand) -> int:
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        suite_id = command.suite or project.suite or "standard"
        install_suite(command.project_root, suite_id, self.catalog)
        return 0

    def check(self, command: RunCommand) -> int:
        exit_code, _report = self.run_suite(command, RunMode.CHECK)
        return exit_code

    def format(self, command: RunCommand) -> int:
        exit_code, _report = self.run_suite(command, RunMode.APPLY)
        return exit_code

    def run_suite(
        self,
        command: RunCommand,
        mode: RunMode,
        *,
        run_id: str | None = None,
        on_progress: Callable[[RunProgress], None] | None = None,
        write_reports: bool = True,
        emit_failure_output: bool = True,
    ) -> tuple[int, RunReport]:
        return self._run(
            command,
            mode,
            run_id=run_id,
            on_progress=on_progress,
            write_reports=write_reports,
            emit_failure_output=emit_failure_output,
        )

    def _run(
        self,
        command: RunCommand,
        mode: RunMode,
        *,
        run_id: str | None = None,
        on_progress: Callable[[RunProgress], None] | None = None,
        write_reports: bool = True,
        emit_failure_output: bool = True,
    ) -> tuple[int, RunReport]:
        context = self._prepare_run_context(command, mode)
        run_id = run_id or generate_run_id()
        check_reports = self._run_all_checks(
            command=command,
            mode=mode,
            context=context,
            run_id=run_id,
            on_progress=on_progress,
        )
        report = self._build_run_report(
            run_id=run_id,
            suite_id=context.suite_id,
            mode=mode,
            check_reports=check_reports,
        )
        if report.status == "failed":
            error_format = command.error_format or context.project.error_format
            if command.ci:
                error_format = "github"
            return self._finalize_failed_run(
                command,
                context.project_root,
                report,
                error_format,
                write_reports=write_reports,
                emit_failure_output=emit_failure_output,
            )
        return self._finalize_successful_run(
            command,
            context.project_root,
            report,
            write_reports=write_reports,
        )

    def _prepare_run_context(self, command: RunCommand, mode: RunMode):
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        project_root = command.project_root.resolve()
        suite_id, tool_ids = resolve_runnables(
            mode=mode,
            project=project,
            catalog=self.catalog,
            suite_override=command.suite,
            check_override=command.check,
        )
        environment = resolve_environment(project_root, project.env)
        scope = resolve_scope(project_root, project, target_override=command.target)
        return _RunContext(
            project=project,
            project_root=project_root,
            suite_id=suite_id,
            tool_ids=tuple(tool_ids),
            environment=environment,
            scope=scope,
            paths=scope_paths(scope),
        )

    def _run_all_checks(
        self,
        *,
        command: RunCommand,
        mode: RunMode,
        context: _RunContext,
        run_id: str,
        on_progress: Callable[[RunProgress], None] | None,
    ) -> list[CheckReport]:
        options = NormalizedOptions(
            paths=context.paths,
            format="json",
            verbose=command.verbose,
            quiet=command.quiet,
            check=mode == RunMode.CHECK if mode == RunMode.APPLY else None,
        )
        check_reports: list[CheckReport] = []
        checks_total = len(context.tool_ids)
        for index, tool_id in enumerate(context.tool_ids):
            self._emit_progress(on_progress, tool_id, index, checks_total)
            check_reports.append(
                self._run_tool_check(
                    tool_id=tool_id,
                    mode=mode,
                    command=command,
                    project=context.project,
                    project_root=context.project_root,
                    paths=context.paths,
                    scope_target=context.scope.target,
                    environment=context.environment,
                    options=options,
                    run_id=run_id,
                )
            )
            self._emit_progress(on_progress, tool_id, index + 1, checks_total)
        return check_reports

    def _build_run_report(
        self,
        *,
        run_id: str,
        suite_id: str,
        mode: RunMode,
        check_reports: list[CheckReport],
    ) -> RunReport:
        status = "passed" if all(r.status == "passed" for r in check_reports) else "failed"
        return RunReport(
            run_id=run_id,
            suite=suite_id,
            mode=mode.value,
            status=status,
            reports=tuple(check_reports),
        )

    def _finalize_successful_run(
        self,
        command: RunCommand,
        project_root: Path,
        report: RunReport,
        *,
        write_reports: bool,
    ) -> tuple[int, RunReport]:
        if write_reports:
            from shipgate.runtime.report_store import ReportStore

            ReportStore(project_root).save(report)
        if command.verbose:
            import sys

            sys.stdout.write(get_formatter("json").render(report))
        return 0, report

    def _emit_progress(
        self,
        on_progress: Callable[[RunProgress], None] | None,
        tool_id: str,
        checks_completed: int,
        checks_total: int,
    ) -> None:
        if on_progress is None:
            return
        on_progress(
            RunProgress(
                current_check_id=tool_id,
                checks_completed=checks_completed,
                checks_total=checks_total,
            )
        )

    def _run_tool_check(
        self,
        *,
        tool_id: str,
        mode: RunMode,
        command: RunCommand,
        project,
        project_root: Path,
        paths,
        scope_target: Path,
        environment,
        options: NormalizedOptions,
        run_id: str,
    ) -> CheckReport:
        tool = self.catalog.get_tool(tool_id)
        config_paths = resolve_config_paths(tool, project, project_root)
        tool_options = NormalizedOptions(
            paths=paths,
            config=config_paths,
            format="json",
            output=options.output,
            verbose=command.verbose,
            quiet=command.quiet,
            check=True if mode == RunMode.CHECK and RunMode.CHECK in tool.modes else None,
        )
        if mode == RunMode.APPLY and RunMode.APPLY in tool.modes:
            tool_options = NormalizedOptions(
                paths=paths,
                config=config_paths,
                verbose=command.verbose,
                quiet=command.quiet,
                check=False,
            )
        request = build_execution_request(
            runnable=tool_id,
            mode=mode if mode in tool.modes else RunMode.CHECK,
            project_root=project_root,
            options=tool_options,
            extra_args=command.extra_args,
        )
        resolved = resolve_request(
            request,
            tool,
            environment,
            target=scope_target,
        )
        return self._execute_check(resolved, run_id)

    def _finalize_failed_run(
        self,
        command: RunCommand,
        project_root: Path,
        report: RunReport,
        error_format: str,
        *,
        write_reports: bool,
        emit_failure_output: bool,
    ) -> tuple[int, RunReport]:
        if write_reports:
            report_path = write_run_report(project_root, report)
            report = RunReport(
                run_id=report.run_id,
                suite=report.suite,
                mode=report.mode,
                status=report.status,
                reports=report.reports,
                report_path=str(report_path.relative_to(project_root)),
            )
        if emit_failure_output:
            output = get_formatter(error_format).render(report)
            if output:
                import sys

                sys.stderr.write(output)
        if write_reports:
            from shipgate.runtime.report_store import ReportStore

            ReportStore(project_root).save(report)
        return 1, report

    def _execute_check(self, resolved: ResolvedRequest, run_id: str) -> CheckReport:
        if self._executor_is_default:
            executable = resolve_executable(
                resolved.tool.executable,
                resolved.environment,
                install_binary=resolved.tool.install.binary if resolved.tool.install else None,
            )
        else:
            executable = resolved.tool.executable
        argv_list = list(build_argv(resolved))
        argv_list[0] = executable
        argv = tuple(argv_list)
        env = dict(resolved.environment.env)
        result = self.executor.run(argv, cwd=resolved.project_root, env=env)
        tool_output = result.stdout
        if resolved.tool.normalizer == "ruff" and resolved.options.output:
            out_file = resolved.options.output
            if out_file.is_file():
                tool_output = out_file.read_text(encoding="utf-8")
        stdout_path, stderr_path, _ = write_raw_output(
            resolved.project_root,
            run_id,
            resolved.tool.id,
            stdout=result.stdout,
            stderr=result.stderr,
            tool_output=tool_output if resolved.tool.normalizer == "ruff" else None,
        )
        normalizer = get_normalizer(resolved.tool.normalizer)
        normalize_result = ProcessResult(
            argv=result.argv,
            cwd=result.cwd,
            exit_code=result.exit_code,
            stdout=tool_output,
            stderr=result.stderr,
            duration_ms=result.duration_ms,
            output_files=result.output_files,
        )
        check_report = normalizer.normalize(resolved, normalize_result)
        return CheckReport(
            check_id=check_report.check_id,
            tool_id=check_report.tool_id,
            status=check_report.status,
            exit_code=check_report.exit_code,
            findings=check_report.findings,
            stdout_path=str(stdout_path.relative_to(resolved.project_root)),
            stderr_path=str(stderr_path.relative_to(resolved.project_root)),
            extra=check_report.extra,
        )

    def list_suites(self) -> str:
        return "\n".join(sorted(self.catalog.suites.keys())) + "\n"

    def list_tools(self) -> str:
        return "\n".join(sorted(self.catalog.tools.keys())) + "\n"

    def list_checks(self) -> str:
        return self.list_tools()

    def schema(self) -> str:
        sample = {
            "schema_version": SCHEMA_VERSION,
            "run_id": "example",
            "suite": "standard",
            "mode": "check",
            "status": "passed",
            "reports": [],
        }
        return json.dumps(sample, indent=2) + "\n"

    def serve(
        self,
        project_root: Path,
        host: str = "127.0.0.1",
        port: int = 8765,
        *,
        open_browser: bool = False,
    ) -> int:
        from shipgate.frontend.server import serve

        serve(project_root, host=host, port=port, open_browser=open_browser)
        return 0

    def lock(self, project_root: Path) -> int:
        manifest = project_root / ".shipgate" / "tools" / "manifest.json"
        packages: dict[str, str] = {}
        if manifest.is_file():
            data = json.loads(manifest.read_text(encoding="utf-8"))
            packages = {k: str(v) for k, v in data.get("packages", {}).items()}
        write_lockfile(project_root / ".shipgate" / "lock.json", packages)
        return 0

    def baseline_update(self, command: RunCommand) -> int:
        exit_code, report = self.run_suite(command, RunMode.CHECK)
        if exit_code != 0:
            return exit_code
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        baseline_report = RunReport(
            run_id="baseline",
            suite=project.suite,
            mode="check",
            status="passed",
            reports=report.reports,
        )
        save_baseline(command.project_root, baseline_report)
        return 0

    def baseline_show(self, project_root: Path) -> str:
        baseline = load_baseline(project_root)
        if baseline is None:
            return "no baseline\n"
        return json.dumps(baseline.to_dict(), indent=2) + "\n"

    def run_batch(self, project_root: Path, batch_path: Path) -> int:
        from shipgate.batch import load_batch_file

        requests = load_batch_file(batch_path)
        worst = 0
        for req in requests:
            cmd = RunCommand(
                project_root=project_root,
                check=req.runnable,
                target=req.target,
                extra_args=req.extra_args,
            )
            code = self.format(cmd) if req.mode == RunMode.APPLY else self.check(cmd)
            worst = max(worst, code)
        return worst

    def gates_init(self, project_root: Path, name: str) -> str:
        path = init_gate(project_root, name)
        return f"created gate: {path}\n"
