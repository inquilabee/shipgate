"""Bandit JSON normalizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.output import normalize_json_items

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class BanditNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult):
        return normalize_json_items(
            request,
            result,
            items_key="results",
            item_to_finding=item_to_finding,
            invalid_message="bandit output must be a JSON object",
            allow_empty_on_success=True,
        )


def item_to_finding(item: dict, check_id: str) -> Finding:
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
