"""Run finalization helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.ci import is_ci_environment, write_github_step_summary
from shipgate.formatters import get_formatter
from shipgate.runtime.report_store import ReportStore

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.reports import RunReport
    from shipgate.domain.run_command import RunCommand
    from shipgate.runtime.session.context import RunProgress


def emit_progress(
    on_progress: Callable[[RunProgress], None] | None,
    tool_id: str,
    checks_completed: int,
    checks_total: int,
) -> None:
    if on_progress is None:
        return
    from shipgate.runtime.session.context import RunProgress

    on_progress(
        RunProgress(
            current_check_id=tool_id,
            checks_completed=checks_completed,
            checks_total=checks_total,
        )
    )


def finalize_successful_run(
    command: RunCommand,
    project_root: Path,
    report: RunReport,
    *,
    write_reports: bool,
) -> tuple[int, RunReport]:
    if write_reports:
        report = ReportStore(project_root).save_final(report)
    if command.verbose:
        import sys

        sys.stdout.write(get_formatter("json").render(report))
    return 0, report


def finalize_failed_run(
    command: RunCommand,
    project_root: Path,
    report: RunReport,
    error_format: str,
    *,
    write_reports: bool,
    emit_failure_output: bool,
) -> tuple[int, RunReport]:
    if write_reports:
        report = ReportStore(project_root).save_final(report)
    if emit_failure_output and not command.quiet:
        output = get_formatter(error_format).render(report)
        if output:
            import sys

            sys.stderr.write(output)
    if command.ci or is_ci_environment():
        write_github_step_summary(f"## ShipGate {report.mode}\n\nStatus: **{report.status}**\n")
    return 1, report
