"""Suite run lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.run_command import RunCommand
from shipgate.runtime.reports import generate_run_id
from shipgate.runtime.session.check_runner import CheckRunner, build_run_report
from shipgate.runtime.session.context import (
    RunContext,
    RunProgress,
    prepare_context,
    resolve_error_format,
)
from shipgate.runtime.session.finalizer import (
    finalize_failed_run,
    finalize_successful_run,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.modes import RunMode
    from shipgate.domain.reports import RunReport
    from shipgate.runtime.session.check_runner import ExecutorProtocol


class RunSession:
    def __init__(
        self,
        *,
        catalog: Catalog,
        executor: ExecutorProtocol,
        executor_is_default: bool,
    ) -> None:
        self._catalog = catalog
        self._runner = CheckRunner(
            catalog=catalog,
            executor=executor,
            executor_is_default=executor_is_default,
        )

    def run(
        self,
        command: RunCommand,
        mode: RunMode,
        *,
        run_id: str | None = None,
        on_progress: Callable[[RunProgress], None] | None = None,
        write_reports: bool = True,
        emit_failure_output: bool = True,
        should_cancel: Callable[[], bool] | None = None,
    ) -> tuple[int, RunReport]:
        context = prepare_context(command, mode, self._catalog)
        run_id = run_id or generate_run_id()
        check_reports = self._runner.run_all_checks(
            command=command,
            context=context,
            run_id=run_id,
            on_progress=on_progress,
            should_cancel=should_cancel,
        )
        report = build_run_report(
            run_id=run_id,
            suite_id=context.suite_id,
            mode=mode,
            check_reports=check_reports,
        )
        error_format = resolve_error_format(command, context.project)
        if report.status == "failed":
            return finalize_failed_run(
                command,
                context.project_root,
                report,
                error_format,
                write_reports=write_reports,
                emit_failure_output=emit_failure_output,
            )
        from shipgate.ci import is_ci_environment, write_github_step_summary

        if command.ci or is_ci_environment():
            write_github_step_summary(f"## ShipGate {mode.value}\n\nStatus: **{report.status}**\n")
        return finalize_successful_run(
            command,
            context.project_root,
            report,
            write_reports=write_reports,
        )


__all__ = [
    "RunCommand",
    "RunContext",
    "RunProgress",
    "RunSession",
]
