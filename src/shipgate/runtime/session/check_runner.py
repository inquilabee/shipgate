"""Check execution during a run session."""

from __future__ import annotations

import shlex
import sys
from typing import TYPE_CHECKING, Protocol

from shipgate.adapter.argv import build_argv
from shipgate.domain.reports import CheckReport, RunReport
from shipgate.gates.runtime import is_gate_tool, prepare_gate_execution
from shipgate.normalize import get_normalizer
from shipgate.runtime.check_cache import CheckResultCache
from shipgate.runtime.environment import resolve_executable
from shipgate.runtime.parallel import run_parallel
from shipgate.runtime.reports import write_raw_output
from shipgate.runtime.session.check_planner import prepare_check
from shipgate.runtime.session.finalizer import emit_progress

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.domain.modes import RunMode
    from shipgate.domain.project import ProjectConfig
    from shipgate.planning.workflow import PlannedCheck
    from shipgate.runtime.executor import ProcessResult
    from shipgate.runtime.session.context import RunCommand, RunContext


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


class CheckRunner:
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

    def run_all_checks(
        self,
        *,
        command: RunCommand,
        context: RunContext,
        run_id: str,
        on_progress: Callable[..., None] | None,
    ) -> list[CheckReport]:
        checks_total = len(context.planned_checks)

        def run_one(planned: PlannedCheck) -> CheckReport:
            report = self.run_planned_check(
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
            emit_progress(on_progress, planned.tool_id, index, checks_total)
            emit_progress(on_progress, planned.tool_id, index + 1, checks_total)
        return reports

    def run_planned_check(
        self,
        *,
        planned: PlannedCheck,
        command: RunCommand,
        context: RunContext,
        run_id: str,
    ) -> CheckReport:
        prepared = prepare_check(
            planned=planned,
            command=command,
            context=context,
            catalog=self._catalog,
        )
        if prepared.report is not None:
            if command.display_cli:
                sys.stderr.write(f"{planned.tool_id}: (skipped: no matching files in scope)\n")
            return prepared.report
        if prepared.request is None:
            raise RuntimeError(
                f"prepare_check returned neither report nor request for {planned.tool_id}"
            )
        return self.execute_check(
            prepared.request,
            run_id,
            project=context.project,
            display_cli=command.display_cli,
            no_cache=command.no_cache,
        )

    def execute_check(
        self,
        resolved: ResolvedRequest,
        run_id: str,
        project: ProjectConfig | None = None,
        *,
        display_cli: bool = False,
        no_cache: bool = False,
    ) -> CheckReport:
        cache = CheckResultCache(resolved.project_root, disabled=no_cache)
        cached = cache.lookup(resolved)
        if cached is not None:
            if display_cli:
                sys.stderr.write(f"{resolved.tool.id}: (cached)\n")
            return cached

        if is_gate_tool(resolved.tool):
            argv, env = prepare_gate_execution(resolved, project=project)
        else:
            if self._executor_is_default:
                executable = resolve_executable(
                    resolved.tool.executable,
                    resolved.environment,
                    install_binary=(
                        resolved.tool.install.binary if resolved.tool.install else None
                    ),
                    project_root=resolved.project_root,
                )
            else:
                executable = resolved.tool.executable
            argv_list = list(build_argv(resolved))
            argv_list[0] = executable
            argv = tuple(argv_list)
            env = dict(resolved.environment.env)
        if display_cli:
            sys.stderr.write(f"{resolved.tool.id}: {shlex.join(argv)}\n")
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
        report = CheckReport(
            check_id=check_report.check_id,
            tool_id=check_report.tool_id,
            status=check_report.status,
            exit_code=check_report.exit_code,
            findings=check_report.findings,
            stdout_path=str(stdout_path.relative_to(resolved.project_root)),
            stderr_path=str(stderr_path.relative_to(resolved.project_root)),
            extra=check_report.extra,
        )
        cache.store(resolved, report)
        return report


def build_run_report(
    *,
    run_id: str,
    suite_id: str,
    mode: RunMode,
    check_reports: list[CheckReport],
) -> RunReport:
    status = "passed" if all(report.status == "passed" for report in check_reports) else "failed"
    return RunReport(
        run_id=run_id,
        suite=suite_id,
        mode=mode.value,
        status=status,
        reports=tuple(check_reports),
    )
