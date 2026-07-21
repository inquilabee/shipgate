"""Ruff JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class RuffNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult) -> CheckReport:
        check_id = request.tool.id
        if result.exit_code == 0 and not result.stdout.strip():
            return CheckReport(
                check_id=check_id,
                tool_id=check_id,
                status="passed",
                exit_code=0,
            )
        try:
            items = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError as exc:
            raise NormalizationError(f"invalid ruff JSON output: {exc}") from exc
        if not isinstance(items, list):
            raise NormalizationError("ruff output must be a JSON array")
        findings: list[Finding] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            location = None
            loc = item.get("location") or {}
            filename = item.get("filename") or item.get("file_name")
            if filename:
                location = FindingLocation(
                    path=str(filename),
                    line=loc.get("row") or item.get("line"),
                    column=loc.get("column") or item.get("column"),
                )
            findings.append(
                Finding(
                    check_id=check_id,
                    rule_id=str(item.get("code") or item.get("rule") or "UNKNOWN"),
                    severity=str(item.get("severity") or "error"),
                    message=str(item.get("message") or ""),
                    location=location,
                    extra={"raw": dict(item)},
                )
            )
        status = "failed" if findings or result.exit_code != 0 else "passed"
        return CheckReport(
            check_id=check_id,
            tool_id=check_id,
            status=status,
            exit_code=result.exit_code,
            findings=tuple(findings),
        )
