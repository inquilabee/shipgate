"""Semgrep JSON normalizer."""

from __future__ import annotations

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.json_base import JsonItemsNormalizer


class SemgrepNormalizer(JsonItemsNormalizer):
    items_key = "results"
    invalid_message = "semgrep output must be a JSON object"
    decode_error = "invalid semgrep JSON output"

    def item_to_finding(self, item: dict, check_id: str) -> Finding:
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
            message=str(item.get("message") or extra.get("message") or "semgrep finding"),
            location=location,
            extra={"raw": dict(item)},
        )
