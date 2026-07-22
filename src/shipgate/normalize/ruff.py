"""Ruff JSON normalizer."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding
from shipgate.normalize.core.json import JsonItemsNormalizer
from shipgate.normalize.core.location import location_from_item


class RuffNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "ruff output must be a JSON array"
    decode_error = "invalid ruff JSON output"

    def _item_location(self, item: dict[str, Any]):
        return location_from_item(
            item,
            path_keys=("filename", "file_name"),
            line_keys=("row", "line"),
            column_keys=("column",),
            nested_location_key="location",
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
