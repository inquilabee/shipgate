"""Ruff JSON normalizer."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.normalize.core.json import JsonItemsNormalizer


class RuffNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "ruff output must be a JSON array"
    decode_error = "invalid ruff JSON output"

    def _item_location(self, item: dict[str, Any]) -> FindingLocation | None:
        loc = item.get("location") or {}
        filename = item.get("filename") or item.get("file_name")
        if not filename:
            return None
        return FindingLocation(
            path=str(filename),
            line=loc.get("row") or item.get("line"),
            column=loc.get("column") or item.get("column"),
        )

    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding:
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("code") or item.get("rule") or "UNKNOWN"),
            severity=str(item.get("severity") or "error"),
            message=str(item.get("message") or ""),
            location=self._item_location(item),
            extra={"raw": dict(item)},
        )
