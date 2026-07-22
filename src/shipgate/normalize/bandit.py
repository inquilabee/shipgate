"""Bandit JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.output import read_tool_output, tool_exit_report

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class BanditNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        stdout = read_tool_output(request, result)
        if result.exit_code == 0 and not stdout.strip():
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="passed",
                exit_code=0,
            )
        try:
            payload = json.loads(stdout) if stdout.strip() else {}
        except json.JSONDecodeError:
            if result.exit_code == 0:
                return CheckReport(
                    check_id=check_id,
                    tool_id=check_id,
                    status="passed",
                    exit_code=0,
                )
            return tool_exit_report(check_id, result)
        if not isinstance(payload, dict):
            raise NormalizationError("bandit output must be a JSON object")
        items = payload.get("results", [])
        if not isinstance(items, list):
            raise NormalizationError("bandit results must be a JSON array")
        findings = tuple(
            _item_to_finding(item, check_id) for item in items if isinstance(item, dict)
        )
        status = "failed" if findings or result.exit_code != 0 else "passed"
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status=status,
            exit_code=result.exit_code,
            findings=findings,
        )


def _item_to_finding(item: dict, check_id: str) -> Finding:
    location = None
    filename = item.get("filename")
    if filename:
        location = FindingLocation(
            path=str(filename),
            line=item.get("line_number"),
            column=item.get("col_offset"),
        )
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("test_id") or "BANDIT"),
        severity=str(item.get("issue_severity") or "error").lower(),
        message=str(item.get("issue_text") or item.get("issue_cwe") or "bandit finding"),
        location=location,
        extra={"raw": dict(item)},
    )
