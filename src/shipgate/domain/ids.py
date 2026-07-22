"""ID validation helpers."""

from __future__ import annotations

import re

ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def validate_id(value: str, *, kind: str = "id") -> str:
    if not value:
        raise ValueError(f"{kind} must not be empty")
    if "/" in value or "\\" in value or " " in value:
        raise ValueError(f"invalid {kind}: {value!r}")
    if value != value.lower():
        raise ValueError(f"{kind} must be lowercase: {value!r}")
    if not ID_PATTERN.match(value):
        raise ValueError(f"invalid {kind}: {value!r}")
    return value
