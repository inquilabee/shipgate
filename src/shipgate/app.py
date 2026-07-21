"""Application service layer."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from shipgate.adapter.argv import build_argv
from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.baseline import load_baseline, save_baseline
from shipgate.catalog.loader import load_catalog
from shipgate.ci import apply_ci_defaults, is_ci_environment, write_github_step_summary
from shipgate.config.loader import load_config
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport, RunReport, report_json_schema
from shipgate.formatters.plugins import get_formatter
from shipgate.gates.catalog import merge_gate_catalog
from shipgate.gates.init import init_gate
from shipgate.normalize.base import get_normalizer
from shipgate.planning.checks import list_project_checks
from shipgate.planning.incremental import filter_changed
from shipgate.planning.requests import build_execution_request, resolve_request
from shipgate.planning.scopes import resolve_scope, scope_paths
from shipgate.planning.workflow import PlannedCheck, resolve_runnables, suite_execution_flags
from shipgate.runtime.environment import resolve_environment, resolve_executable
from shipgate.runtime.executor import Executor, ProcessResult
from shipgate.runtime.install import install_suite
from shipgate.runtime.lockfile import write_lockfile
from shipgate.runtime.parallel import run_parallel
from shipgate.runtime.reports import generate_run_id, write_raw_output, write_run_report

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
    from shipgate.domain.project import ProjectConfig, Scope


@dataclass(frozen=True)
class RunCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None
    check: str | None = None
    workflow: str | None = None
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
    planned_checks: tuple[PlannedCheck, ...]
    environment: ExecutionEnvironment
    default_scope: Scope
    parallel: bool
    fail_fast: bool


class ExecutorProtocol(Protocol):
    def run(
        self,
        argv: tuple[str, ...],
        *,
        cwd: Path,
        env: dict[str, str] | None = None,
    ) -> ProcessResult: ...


class _FailFastError(Exception):
    def __init__(self, report: CheckReport) -> None:
        self.report = report


class ShipGateApp:
    def __init__(
        self,
        *,
        catalog: Catalog | None = None,
        executor: ExecutorProtocol | None = None,
    ) -> None:
        self._base_catalog = catalog or load_catalog()
        self._executor_is_default = executor is None
        self.executor = executor or Executor()

    def _catalog_for(self, project_root: Path) -> Catalog:
        return merge_gate_catalog(self._base_catalog, project_root)

    def install(self, command: InstallCommand) -> int:
        catalog = self._catalog_for(command.project_root)
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        suite_id = command.suite or project.suite or "standard"
        install_suite(command.project_root, suite_id, catalog)
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
        catalog = self._catalog_for(command.project_root)
        context = self._prepare_run_context(command, mode, catalog)
        run_id = run_id or generate_run_id()
        check_reports = self._run_all_checks(
            command=command,
            context=context,
            catalog=catalog,
            run_id=run_id,
            on_progress=on_progress,
        )
        report = self._build_run_report(
            run_id=run_id,
            suite_id=context.suite_id,
            mode=mode,
            check_reports=check_reports,
        )
        error_format = self._resolve_error_format(command, context.project)
        if report.status == "failed":
            return self._finalize_failed_run(
                command,
                context.project_root,
                report,
                error_format,
                write_reports=write_reports,
                emit_failure_output=emit_failure_output,
            )
        if command.ci or is_ci_environment():
            write_github_step_summary(
                f"## ShipGate {mode.value}\n\nStatus: **{report.status}**\n"
            )
        return self._finalize_successful_run(
            command,
            context.project_root,
            report,
            write_reports=write_reports,
        )

    def _resolve_error_format(self, command: RunCommand, project: ProjectConfig) -> str:
        explicit = command.error_format or project.error_format
        if command.ci or is_ci_environment():
            return apply_ci_defaults(explicit)
        return explicit or "json"

    def _prepare_run_context(
        self,
        command: RunCommand,
        mode: RunMode,
        catalog: Catalog,
    ) -> _RunContext:
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        project_root = command.project_root.resolve()
        suite_id, planned_checks = resolve_runnables(
            mode=mode,
            project=project,
            catalog=catalog,
            suite_override=command.suite,
            check_override=command.check,
            workflow_override=command.workflow,
        )
        parallel, fail_fast = suite_execution_flags(catalog, suite_id, project)
        environment = resolve_environment(project_root, project.env)
        default_scope = resolve_scope(project_root, project, target_override=command.target)
        return _RunContext(
            project=project,
            project_root=project_root,
            suite_id=suite_id,
            planned_checks=tuple(planned_checks),
            environment=environment,
            default_scope=default_scope,
            parallel=parallel,
            fail_fast=fail_fast,
        )

    def _run_all_checks(
        self,
        *,
        command: RunCommand,
        context: _RunContext,
        catalog: Catalog,
        run_id: str,
        on_progress: Callable[[RunProgress], None] | None,
    ) -> list[CheckReport]:
        checks_total = len(context.planned_checks)

        def run_one(planned: PlannedCheck) -> CheckReport:
            report = self._run_planned_check(
                planned=planned,
                command=command,
                context=context,
                catalog=catalog,
                run_id=run_id,
            )
            if context.fail_fast and report.status == "failed":
                raise _FailFastError(report)
            return report

        if context.parallel:
            try:
                reports = run_parallel(
                    list(context.planned_checks),
                    run_one,
                    fail_fast=context.fail_fast,
                )
            except _FailFastError as exc:
                reports = [exc.report]
        else:
            reports = []
            for planned in context.planned_checks:
                try:
                    report = run_one(planned)
                except _FailFastError as exc:
                    reports.append(exc.report)
                    break
                reports.append(report)
        for index, planned in enumerate(context.planned_checks[: len(reports)]):
            self._emit_progress(on_progress, planned.tool_id, index, checks_total)
            self._emit_progress(on_progress, planned.tool_id, index + 1, checks_total)
        return reports

    def _run_planned_check(
        self,
        *,
        planned: PlannedCheck,
        command: RunCommand,
        context: _RunContext,
        catalog: Catalog,
        run_id: str,
    ) -> CheckReport:
        scope = resolve_scope(
            context.project_root,
            context.project,
            target_override=command.target,
            scope_name=planned.scope_name,
        )
        paths = scope_paths(scope, context.project_root, mode=planned.mode)
        paths = filter_changed(
            paths,
            command.since,
            project_root=context.project_root,
            changed_only=command.changed_only,
        )
        tool = catalog.get_tool(planned.tool_id)
        config_paths = resolve_config_paths(tool, context.project, context.project_root)
        exclude = (
            tuple(entry.rstrip("/") for entry in scope.exclude) if "exclude" in tool.cli else ()
        )
        tool_options = NormalizedOptions(
            paths=paths,
            config=config_paths,
            exclude=exclude,
            verbose=command.verbose,
            quiet=command.quiet,
            check=True if planned.mode == RunMode.CHECK and RunMode.CHECK in tool.modes else None,
        )
        if planned.mode == RunMode.APPLY and RunMode.APPLY in tool.modes:
            tool_options = NormalizedOptions(
                paths=paths,
                config=config_paths,
                verbose=command.verbose,
                quiet=command.quiet,
                check=False,
            )
        request = build_execution_request(
            runnable=planned.tool_id,
            mode=planned.mode if planned.mode in tool.modes else RunMode.CHECK,
            project_root=context.project_root,
            options=tool_options,
            extra_args=command.extra_args,
        )
        resolved = resolve_request(
            request,
            tool,
            context.environment,
            target=scope.target,
            project=context.project,
        )
        return self._execute_check(resolved, run_id)

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
        if emit_failure_output and not command.quiet:
            output = get_formatter(error_format).render(report)
            if output:
                import sys

                sys.stderr.write(output)
        if write_reports:
            from shipgate.runtime.report_store import ReportStore

            ReportStore(project_root).save(report)
        if command.ci or is_ci_environment():
            write_github_step_summary(
                f"## ShipGate {report.mode}\n\nStatus: **{report.status}**\n"
            )
        return 1, report

    def _execute_check(self, resolved: ResolvedRequest, run_id: str) -> CheckReport:
        if self._executor_is_default:
            executable = resolve_executable(
                resolved.tool.executable,
                resolved.environment,
                install_binary=resolved.tool.install.binary if resolved.tool.install else None,
                project_root=resolved.project_root,
            )
        else:
            executable = resolved.tool.executable
        argv_list = list(build_argv(resolved))
        argv_list[0] = executable
        argv = tuple(argv_list)
        env = dict(resolved.environment.env)
        result = self.executor.run(argv, cwd=resolved.project_root, env=env)
        stdout_path, stderr_path, _ = write_raw_output(
            resolved.project_root,
            run_id,
            resolved.tool.id,
            stdout=result.stdout,
            stderr=result.stderr,
        )
        normalizer = get_normalizer(resolved.tool.normalizer)
        check_report = normalizer.normalize(resolved, result)
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
        catalog = self._base_catalog
        lines = sorted(catalog.suites.keys())
        if catalog.workflows:
            lines.extend(sorted(catalog.workflows.keys()))
        return "\n".join(sorted(set(lines))) + "\n"

    def list_tools(self) -> str:
        return "\n".join(sorted(self._base_catalog.tools.keys())) + "\n"

    def list_checks(self, project_root: Path | None = None) -> str:
        if project_root is None:
            from shipgate.paths import find_project_root

            project_root = find_project_root()
        project = load_config(project_root=project_root)
        catalog = self._catalog_for(project_root)
        checks = list_project_checks(project, catalog)
        return "\n".join(checks) + ("\n" if checks else "")

    def schema(self) -> str:
        return json.dumps(report_json_schema(), indent=2) + "\n"

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
