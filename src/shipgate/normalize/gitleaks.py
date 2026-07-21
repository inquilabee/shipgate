"""Gitleaks JSON normalizer."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shipgate.domain.reports import CheckReport, Finding, FindingLocation
from shipgate.errors import NormalizationError

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class GitleaksNormalizer:
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
            payload = json.loads(stdout) if stdout.strip() else []
        except json.JSONDecodeError as exc:
            raise NormalizationError(f"invalid gitleaks JSON output: {exc}") from exc
        if not isinstance(payload, list):
            raise NormalizationError("gitleaks output must be a JSON array")
        findings = tuple(
            _item_to_finding(item, check_id) for item in payload if isinstance(item, dict)
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
    file_path = item.get("File") or item.get("file")
    if file_path:
        location = FindingLocation(
            path=str(file_path),
            line=item.get("StartLine") or item.get("startLine"),
            column=item.get("StartColumn") or item.get("startColumn"),
        )
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("RuleID") or item.get("ruleID") or "GITLEAKS"),
        severity="error",
        message=str(item.get("Description") or item.get("description") or "secret detected"),
        location=location,
        extra={"raw": dict(item)},
    )
