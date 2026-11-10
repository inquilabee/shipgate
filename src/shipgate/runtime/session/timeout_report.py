"""The report for a check whose tool outlived its time limit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding
from shipgate.runtime.reports import write_raw_output

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import CheckTimeoutError

TIMEOUT_EXIT_CODE = 124
TIMEOUT_RULE_ID = "shipgate.timeout"


def timed_out_report(resolved: ResolvedRequest, exc: CheckTimeoutError, run_id: str) -> CheckReport:
    """A failed report for this check only, so the rest of the run still completes."""
    tool_id = resolved.tool.id
    stdout_path, stderr_path, _ = write_raw_output(
        resolved.project_root, run_id, tool_id, stdout=exc.stdout, stderr=exc.stderr
    )
    return CheckReport(
        check_id=tool_id,
        tool_id=tool_id,
        status="failed",
        exit_code=TIMEOUT_EXIT_CODE,
        findings=(
            Finding(
                check_id=tool_id,
                rule_id=TIMEOUT_RULE_ID,
                severity="error",
                message=f"{tool_id} timed out after {exc.timeout_seconds}s",
            ),
        ),
        stdout_path=str(stdout_path.relative_to(resolved.project_root)),
        stderr_path=str(stderr_path.relative_to(resolved.project_root)),
        extra={"error": "timeout", "timeout_seconds": exc.timeout_seconds},
    )
