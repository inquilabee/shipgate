"""ty JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.output import empty_pass_report, findings_report, read_tool_output
from shipgate.normalize.ruff import ruff_item_to_finding

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class TyNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult):
        check_id = request.tool.id
        stdout = read_tool_output(request, result)
        if result.exit_code == 0 and not stdout.strip():
            return empty_pass_report(check_id)
        items = parse_ty_items(stdout)
        findings = tuple(ty_item_to_finding(item, check_id) for item in items)
        return findings_report(check_id, result, findings)


def parse_ty_items(stdout: str) -> list[dict]:
    payload = load_ty_payload(stdout)
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    diagnostics = payload.get("diagnostics")
    if isinstance(diagnostics, list):
        return [item for item in diagnostics if isinstance(item, dict)]
    raise NormalizationError("ty output must be a JSON array of diagnostics")


def load_ty_payload(stdout: str) -> list[dict] | dict:
    try:
        payload = json.loads(stdout) if stdout.strip() else []
    except json.JSONDecodeError as exc:
        raise NormalizationError(f"invalid ty JSON output: {exc}") from exc
    if isinstance(payload, (list, dict)):
        return payload
    raise NormalizationError("ty output must be a JSON array of diagnostics")


def ty_item_to_finding(item: dict, check_id: str) -> Finding:
    if "code" in item or "filename" in item:
        return ruff_item_to_finding(item, check_id)
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("check_name") or item.get("code") or item.get("rule") or "TY"),
        severity=str(item.get("severity") or "error"),
        message=str(item.get("description") or item.get("message") or ""),
        location=ty_location(item),
        extra={"raw": dict(item)},
    )


def ty_location(item: dict) -> FindingLocation | None:
    loc = item.get("location") or {}
    file_path = loc.get("path") or item.get("path") or item.get("file")
    if not file_path:
        return None
    return FindingLocation(
        path=str(file_path),
        line=ty_line(item, loc),
        column=ty_column(item, loc),
    )


def ty_line(item: dict, loc: dict) -> int | None:
    begin = (loc.get("positions") or {}).get("begin") or {}
    return begin.get("line") or loc.get("row") or item.get("line")


def ty_column(item: dict, loc: dict) -> int | None:
    begin = (loc.get("positions") or {}).get("begin") or {}
    return begin.get("column") or loc.get("column") or item.get("column")
