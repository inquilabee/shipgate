"""Bandit JSON normalizer."""

from __future__ import annotations

from shipgate.domain.reports import Finding
from shipgate.normalize.core.json import JsonItemsNormalizer
from shipgate.normalize.core.location import location_from_item


class BanditNormalizer(JsonItemsNormalizer):
    items_key = "results"
    invalid_message = "bandit output must be a JSON object"
    allow_empty_on_success = True

    def item_to_finding(self, item: dict, check_id: str) -> Finding:
        return Finding(
            check_id=check_id,
            rule_id=str(item.get("test_id") or "BANDIT"),
            severity=str(item.get("issue_severity") or "error").lower(),
            message=str(item.get("issue_text") or item.get("issue_cwe") or "bandit finding"),
            location=location_from_item(
                item,
                path_keys=("filename",),
                line_keys=("line_number",),
                column_keys=("col_offset",),
                nested_location_key=None,
            ),
            extra={"raw": dict(item)},
        )
