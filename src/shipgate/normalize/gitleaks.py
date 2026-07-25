"""Gitleaks JSON normalizer."""

from __future__ import annotations

from shipgate.domain.reports import Finding
from shipgate.normalize.core import JsonItemsNormalizer, location_from_item


class GitleaksNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "gitleaks output must be a JSON array"
    decode_error = "invalid gitleaks JSON output"

    def item_to_finding(self, item: dict, check_id: str) -> Finding:  # ruff:ignore[no-self-use]
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("RuleID") or item.get("ruleID") or "GITLEAKS"),
            severity="error",
            message=str(item.get("Description") or item.get("description") or "secret detected"),
            location=location_from_item(
                item,
                path_keys=("File", "file"),
                line_keys=("StartLine", "startLine"),
                column_keys=("StartColumn", "startColumn"),
                nested_location_key=None,
            ),
            extra={"raw": dict(item)},
        )
