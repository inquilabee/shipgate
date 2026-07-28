"""Gate report payload helpers."""

from __future__ import annotations

import contextlib
from typing import Any


def gate_finding_payload(
    *,
    rule_id: str,
    severity: str,
    message: str,
    file: str = "",
    line: str | int | None = None,
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
    }
    if file:
        location: dict[str, Any] = {"file": file}
        if line not in (None, ""):
            with contextlib.suppress(ValueError):
                location["line"] = line if isinstance(line, int) else int(line)
        finding["location"] = location
    return finding
