"""Generic exit-code normalizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class GenericExitNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        if result.exit_code == 0:
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="passed",
                exit_code=0,
            )
        message = result.stderr.strip() or result.stdout.strip() or "Tool failed"
        finding = Finding(
            check_id=check_id,
            rule_id="TOOL_EXIT",
            severity="error",
            message=message,
            location=None,
        )
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status="failed",
            exit_code=result.exit_code,
            findings=(finding,),
        )
