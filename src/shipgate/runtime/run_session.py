"""Suite run lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from shipgate.adapter.argv import build_argv
from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.ci import apply_ci_defaults, is_ci_environment, write_github_step_summary
from shipgate.config.loader import load_config
from shipgate.domain.modes import RunMode
from shipgate.domain.options import NormalizedOptions
from shipgate.domain.reports import CheckReport, RunReport
from shipgate.formatters import get_formatter
from shipgate.gates.runtime import is_gate_tool, prepare_gate_execution
from shipgate.normalize import get_normalizer
from shipgate.planning.incremental import filter_changed
from shipgate.planning.requests import build_execution_request, resolve_request
from shipgate.planning.scopes import resolve_scope, scope_paths_for_tool
from shipgate.planning.workflow import PlannedCheck, resolve_runnables, suite_execution_flags
from shipgate.runtime.environment import resolve_environment, resolve_executable
from shipgate.runtime.parallel import run_parallel
from shipgate.runtime.reports import generate_run_id, write_raw_output, write_run_report

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ExecutionEnvironment, ResolvedRequest
    from shipgate.domain.project import ProjectConfig, Scope
    from shipgate.runtime.executor import ProcessResult


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
class RunProgress:
    current_check_id: str
    checks_completed: int
    checks_total: int


@dataclass(frozen=True)
class RunContext:
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


class FailFastError(Exception):
    def __init__(self, report: CheckReport) -> None:
        self.report = report


class RunSession:
    def __init__(
        self,
        *,
        catalog: Catalog,
        executor: ExecutorProtocol,
        executor_is_default: bool,
    ) -> None:
        self._catalog = catalog
        self._executor = executor
        self._executor_is_default = executor_is_default

    def run(
        self,
        command: RunCommand,
        mode: RunMode,
        *,
        run_id: str | None = None,
        on_progress: Callable[[RunProgress], None] | None = None,
        write_reports: bool = True,
        emit_failure_output: bool = True,
    ) -> tuple[int, RunReport]:
        context = self._prepare_context(command, mode)
        run_id = run_id or generate_run_id()
        check_reports = self._run_all_checks(
            command=command,
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
            write_github_step_summary(f"## ShipGate {mode.value}\n\nStatus: **{report.status}**\n")
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

    def _prepare_context(self, command: RunCommand, mode: RunMode) -> RunContext:
        project = load_config(
            config_path=command.config_path,
            project_root=command.project_root,
        )
        project_root = command.project_root.resolve()
        suite_id, planned_checks = resolve_runnables(
            mode=mode,
            project=project,
            catalog=self._catalog,
            suite_override=command.suite,
            check_override=command.check,
            workflow_override=command.workflow,
        )
        parallel, fail_fast = suite_execution_flags(self._catalog, suite_id, project)
        environment = resolve_environment(project_root, project.env)
        default_scope = resolve_scope(project_root, project, target_override=command.target)
        return RunContext(
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
        context: RunContext,
        run_id: str,
        on_progress: Callable[[RunProgress], None] | None,
    ) -> list[CheckReport]:
        checks_total = len(context.planned_checks)

        def run_one(planned: PlannedCheck) -> CheckReport:
            report = self._run_planned_check(
                planned=planned,
                command=command,
                context=context,
                run_id=run_id,
            )
            if context.fail_fast and report.status == "failed":
                raise FailFastError(report)
            return report

        if context.parallel:
            try:
                reports = run_parallel(
                    list(context.planned_checks),
                    run_one,
                    fail_fast=context.fail_fast,
                )
            except FailFastError as exc:
                reports = [exc.report]
        else:
            reports = []
            for planned in context.planned_checks:
                try:
                    report = run_one(planned)
                except FailFastError as exc:
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
        context: RunContext,
        run_id: str,
    ) -> CheckReport:
        scope = resolve_scope(
            context.project_root,
            context.project,
            target_override=command.target,
            scope_name=planned.scope_name,
        )
        tool = self._catalog.get_tool(planned.tool_id)
        paths = scope_paths_for_tool(
            scope,
            tool,
            context.project_root,
            mode=planned.mode,
        )
        paths = filter_changed(
            paths,
            command.since,
            project_root=context.project_root,
            changed_only=command.changed_only,
        )
        if not paths and tool.scope.delivery != "root":
            return CheckReport(
                check_id=planned.tool_id,
                tool_id=planned.tool_id,
                status="passed",
                exit_code=0,
                extra={"skipped": "no matching files in scope"},
            )
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
        return self._execute_check(resolved, run_id, project=context.project)

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
            write_github_step_summary(f"## ShipGate {report.mode}\n\nStatus: **{report.status}**\n")
        return 1, report

    def _execute_check(
        self,
        resolved: ResolvedRequest,
        run_id: str,
        project: ProjectConfig | None = None,
    ) -> CheckReport:
        if is_gate_tool(resolved.tool):
            argv, env = prepare_gate_execution(resolved, project=project)
        else:
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
        result = self._executor.run(argv, cwd=resolved.project_root, env=env)
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
