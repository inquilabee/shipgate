"""Ruff JSON normalizer."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shipgate.normalize.core import JsonItemsNormalizer, ruff_like_finding

if TYPE_CHECKING:
    from shipgate.domain.reports import Finding


class RuffNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "ruff output must be a JSON array"
    decode_error = "invalid ruff JSON output"

    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding:
        return ruff_like_finding(item, check_id)
