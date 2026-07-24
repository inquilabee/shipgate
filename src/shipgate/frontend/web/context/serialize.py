"""Finding and requirements serialization helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.frontend.domain.models import FindingRecord

REQUIREMENTS_PATH = Path(__file__).resolve().parents[2] / "static" / "requirements.txt"


@lru_cache(maxsize=1)
def requirements_text() -> str:
    return REQUIREMENTS_PATH.read_text(encoding="utf-8").strip()


def finding_to_api(finding: FindingRecord) -> dict[str, object]:
    return {
        "id": finding.id,
        "check_id": finding.check_id,
        "tool_id": finding.tool_id,
        "rule_id": finding.rule_id,
        "severity": finding.severity,
        "message": finding.message,
        "file": finding.file,
        "line": finding.line,
        "column": finding.column,
        "category": finding.category.value,
    }
