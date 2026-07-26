"""deptry JSON normalizer."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding
from shipgate.normalize.core import JsonItemsNormalizer, location_from_item


class DeptryNormalizer(JsonItemsNormalizer):
    items_key = None
    invalid_message = "deptry output must be a JSON array"
    allow_empty_on_success = True

    def item_to_finding(self, item: dict[str, Any], check_id: str) -> Finding:  # ruff:ignore[no-self-use]
        error = item.get("error")
        error_dict = error if isinstance(error, dict) else {}
        code = str(error_dict.get("code") or "DEP")
        message = str(error_dict.get("message") or item.get("module") or "deptry finding")
        module = item.get("module")
        if module and str(module) not in message:
            message = f"{module}: {message}"
        return Finding(
            check_id=check_id,
            rule_id=code,
            severity="error",
            message=message,
            location=location_from_item(
                item,
                path_keys=("file",),
                line_keys=("line",),
                column_keys=("column",),
                nested_location_key="location",
            ),
            extra={"raw": dict(item)},
        )
