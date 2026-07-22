"""ty JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.output import read_tool_output
from shipgate.normalize.ruff import ruff_item_to_finding

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class TyNormalizer:
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
        items = parse_ty_items(stdout)
        findings = tuple(ty_item_to_finding(item, check_id) for item in items)
        status = "failed" if findings or result.exit_code != 0 else "passed"
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status=status,
            exit_code=result.exit_code,
            findings=findings,
        )


def parse_ty_items(stdout: str) -> list[dict]:
    try:
        payload = json.loads(stdout) if stdout.strip() else []
    except json.JSONDecodeError as exc:
        raise NormalizationError(f"invalid ty JSON output: {exc}") from exc
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and "diagnostics" in payload:
        diagnostics = payload["diagnostics"]
        if isinstance(diagnostics, list):
            return [item for item in diagnostics if isinstance(item, dict)]
    raise NormalizationError("ty output must be a JSON array of diagnostics")


def ty_item_to_finding(item: dict, check_id: str) -> Finding:
    if "code" in item or "filename" in item:
        return ruff_item_to_finding(item, check_id)
    location = None
    loc = item.get("location") or {}
    file_path = loc.get("path") or item.get("path") or item.get("file")
    positions = loc.get("positions") or {}
    begin = positions.get("begin") or {}
    if file_path:
        location = FindingLocation(
            path=str(file_path),
            line=begin.get("line") or loc.get("row") or item.get("line"),
            column=begin.get("column") or loc.get("column") or item.get("column"),
        )
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("check_name") or item.get("code") or item.get("rule") or "TY"),
        severity=str(item.get("severity") or "error"),
        message=str(item.get("description") or item.get("message") or ""),
        location=location,
        extra={"raw": dict(item)},
    )
