"""Finding and requirements serialization helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.frontend.domain.models import FindingRecord, RunRecord

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
        "docs_url": finding.docs_url,
        "suggested_commands": list(finding.suggested_commands),
    }


def run_to_api(run: RunRecord) -> dict[str, object]:
    return {
        "id": run.id,
        "branch": run.branch,
        "suite_id": run.suite_id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "duration_ms": run.duration_ms,
        "finding_count": run.summary.finding_count if run.summary else 0,
        "worktree_path": run.worktree_path,
        "error_message": run.error_message,
        "current_check_id": run.current_check_id,
        "checks_completed": run.checks_completed,
        "checks_total": run.checks_total,
    }
