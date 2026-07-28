"""Shared finding location helpers."""

from __future__ import annotations

from typing import Any

from shipgate.domain.reports import FindingLocation


def finding_location(
    path: str | None,
    *,
    line: int | None = None,
    column: int | None = None,
) -> FindingLocation | None:
    return FindingLocation(path=str(path), line=line, column=column) if path else None


def location_from_item(
    item: dict[str, Any],
    *,
    path_keys: tuple[str, ...],
    line_keys: tuple[str, ...] = (),
    column_keys: tuple[str, ...] = (),
    nested_location_key: str | None = "location",
) -> FindingLocation | None:
    nested = item.get(nested_location_key) if nested_location_key else None
    nested_dict = nested if isinstance(nested, dict) else {}
    path = first_value(item, path_keys) or first_value(nested_dict, path_keys)
    line = first_int(item, line_keys) or first_int(nested_dict, line_keys)
    column = first_int(item, column_keys) or first_int(nested_dict, column_keys)
    return finding_location(str(path) if path is not None else None, line=line, column=column)


def first_value(item: dict[str, Any], keys: tuple[str, ...]) -> object | None:
    for key in keys:
        value = item.get(key)
        if value is not None:
            return value
    return None


def first_int(item: dict[str, Any], keys: tuple[str, ...]) -> int | None:
    value = first_value(item, keys)
    return (
        None
        if value is None
        else (
            value
            if isinstance(value, int)
            else (int(value) if isinstance(value, str) and value.isdigit() else None)
        )
    )
