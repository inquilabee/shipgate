"""Shared policy report writing."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from shipgate.policy.core.finding import PolicyFinding


def write_findings_report(
    findings: Sequence[PolicyFinding],
    report_path: Path | None,
    *,
    extra: Mapping[str, object] | None = None,
) -> None:
    if not report_path:
        return
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, object] = {"findings": [finding.to_dict() for finding in findings]}
    if extra:
        payload.update(extra)
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
