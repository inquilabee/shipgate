"""Shared helpers for reading tool stdout and output files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


def looks_like_json(text: str) -> bool:
    stripped = text.strip()
    return stripped.startswith("{") or stripped.startswith("[")


def read_tool_output(request: ResolvedRequest, result: ProcessResult) -> str:
    stdout = result.stdout
    output_path = request.options.output or request.output_path
    if (
        output_path is not None
        and output_path.is_file()
        and (not stdout.strip() or not looks_like_json(stdout))
    ):
        return output_path.read_text(encoding="utf-8")
    return stdout


def tool_exit_report(check_id: str, result: ProcessResult) -> CheckReport:
    message = result.stderr.strip() or result.stdout.strip() or "Tool failed"
    return CheckReport(
        check_id=check_id,
        tool_id=check_id,
        status="failed",
        exit_code=result.exit_code,
        findings=(
            Finding(
                check_id=check_id,
                rule_id="TOOL_EXIT",
                severity="error",
                message=message,
            ),
        ),
    )
