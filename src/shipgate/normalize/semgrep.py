"""Semgrep JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class SemgrepNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        stdout = result.stdout
        if result.exit_code == 0 and not stdout.strip():
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="passed",
                exit_code=0,
            )
        try:
            payload = json.loads(stdout) if stdout.strip() else {}
        except json.JSONDecodeError as exc:
            raise NormalizationError(f"invalid semgrep JSON output: {exc}") from exc
        if not isinstance(payload, dict):
            raise NormalizationError("semgrep output must be a JSON object")
        items = payload.get("results", [])
        if not isinstance(items, list):
            raise NormalizationError("semgrep results must be a JSON array")
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
    start = item.get("start") or {}
    extra = item.get("extra") or {}
    location = FindingLocation(
        path=str(item.get("path") or ""),
        line=start.get("line"),
        column=start.get("col"),
    )
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("check_id") or extra.get("metadata", {}).get("id") or "SEMGREP"),
        severity=str(extra.get("severity") or "error").lower(),
        message=str(extra.get("message") or item.get("message") or "semgrep finding"),
        location=location,
        extra={"raw": dict(item)},
    )
