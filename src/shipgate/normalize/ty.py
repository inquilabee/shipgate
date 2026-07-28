"""ty JSON normalizer."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding, FindingLocation
from shipgate.errors import NormalizationError
from shipgate.normalize.core import (
    JsonItemsNormalizer,
    dict_items_from_list,
    finding_location,
    is_ruff_like_item,
    ruff_like_finding,
)


class TyNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "ty output must be a JSON array of diagnostics"
    decode_error = "invalid ty JSON output"

    def parse_items(self, payload: object) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return dict_items_from_list(payload)
        if isinstance(payload, dict):
            diagnostics = payload.get("diagnostics")
            if isinstance(diagnostics, list):
                return dict_items_from_list(diagnostics)
        raise NormalizationError(self.invalid_message)

    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding:
        return (
            ruff_like_finding(item, check_id)
            if is_ruff_like_item(item)
            else Finding(
                check_id=check_id,
                rule_id=str(item.get("check_name") or item.get("code") or item.get("rule") or "TY"),
                severity=str(item.get("severity") or "error"),
                message=str(item.get("description") or item.get("message") or ""),
                location=self._item_location(item),
                extra={"raw": dict(item)},
            )
        )

    @staticmethod
    def _item_location(item: dict[str, Any]) -> FindingLocation | None:
        loc = item.get("location") or {}
        file_path = loc.get("path") or item.get("path") or item.get("file")
        return finding_location(
            str(file_path) if file_path else None,
            line=TyNormalizer._line(item, loc),
            column=TyNormalizer._column(item, loc),
        )

    @staticmethod
    def _line(item: dict[str, Any], loc: dict[str, Any]) -> int | None:
        begin = (loc.get("positions") or {}).get("begin") or {}
        return begin.get("line") or loc.get("row") or item.get("line")

    @staticmethod
    def _column(item: dict[str, Any], loc: dict[str, Any]) -> int | None:
        begin = (loc.get("positions") or {}).get("begin") or {}
        return begin.get("column") or loc.get("column") or item.get("column")
