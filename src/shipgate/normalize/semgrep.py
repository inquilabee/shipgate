"""Semgrep JSON normalizer."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.output import normalize_json_items

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest
    from shipgate.runtime.executor import ProcessResult


class SemgrepNormalizer:
    def normalize(self, request: ResolvedRequest, result: ProcessResult):
        return normalize_json_items(
            request,
            result,
            items_key="results",
            item_to_finding=item_to_finding,
            invalid_message="semgrep output must be a JSON object",
            decode_error="invalid semgrep JSON output",
        )


def item_to_finding(item: dict, check_id: str) -> Finding:
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
