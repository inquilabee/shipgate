"""Shared ruff-like diagnostic mapping."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import Finding
from shipgate.normalize.core.location import location_from_item


def ruff_like_finding(item: dict[str, Any], check_id: str) -> Finding:
    return Finding(
        check_id=check_id,
        rule_id=str(item.get("code") or item.get("rule") or "UNKNOWN"),
        severity=str(item.get("severity") or "error"),
        message=str(item.get("message") or ""),
        location=location_from_item(
            item,
            path_keys=("filename", "file_name"),
            line_keys=("row", "line"),
            column_keys=("column",),
            nested_location_key="location",
        ),
        extra={"raw": dict(item)},
    )


def is_ruff_like_item(item: dict[str, Any]) -> bool:
    return "code" in item or "filename" in item
