"""Gate JSON normalizer for shell script gate output."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.normalize.output import read_tool_output, tool_exit_report

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


def _finding_location(raw: dict[str, Any]) -> FindingLocation | None:
    location = raw.get("location")
    if not isinstance(location, dict):
        return None
    path = location.get("path") or location.get("file")
    if not path:
        return None
    line = location.get("line")
    column = location.get("column")
    return FindingLocation(
        path=str(path),
        line=int(line) if line is not None else None,
        column=int(column) if column is not None else None,
    )


def _finding_from_dict(item: dict[str, Any], check_id: str) -> Finding:
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("rule_id") or "gate"),
        severity=str(item.get("severity") or "error").lower(),
        message=str(item.get("message") or "gate finding"),
        location=_finding_location(item),
        extra={"raw": dict(item)},
    )


def _parse_findings(stdout: str, check_id: str) -> tuple[Finding, ...]:
    if not stdout.strip():
        return ()
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return ()
    items: list[Any]
    if isinstance(payload, dict) and "findings" in payload:
        raw_items = payload["findings"]
        items = raw_items if isinstance(raw_items, list) else []
    elif isinstance(payload, list):
        items = payload
    else:
        return ()
    return tuple(_finding_from_dict(item, check_id) for item in items if isinstance(item, dict))


class GateJsonNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        stdout = read_tool_output(request, result)
        findings = _parse_findings(stdout, check_id)
        if findings:
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="failed",
                exit_code=result.exit_code or 1,
                findings=findings,
            )
        if result.exit_code == 0:
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="passed",
                exit_code=0,
            )
        return tool_exit_report(check_id, result)
