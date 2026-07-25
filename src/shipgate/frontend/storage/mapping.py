"""Row mapping helpers for SQLite storage."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunRecord,
    RunStatus,
    RunSummaryRecord,
)
from shipgate.paths import normalize_finding_path

if TYPE_CHECKING:
    import sqlite3


def utc_now() -> datetime:
    return datetime.now(UTC)


def like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def append_clause(
    clauses: list[str], params: list[object], clause: str, value: object | None
) -> None:
    if value is None:
        return
    clauses.append(clause)
    params.append(value)


def findings_filter_clause(
    run_id: str,
    *,
    severity: str | None,
    check_id: str | None,
    file: str | None,
    category: FindingCategory | None,
    rule_id: str | None = None,
) -> tuple[str, list[object]]:
    clauses = ["run_id = ?"]
    params: list[object] = [run_id]
    append_clause(clauses, params, "severity = ?", severity)
    append_clause(clauses, params, "check_id = ?", check_id)
    append_clause(clauses, params, "rule_id = ?", rule_id)
    if file is not None:
        normalized = normalize_finding_path(file) or file
        clauses.append("file LIKE ? ESCAPE '\\'")
        params.append(f"%{like_escape(normalized)}%")
    append_clause(clauses, params, "category = ?", category.value if category else None)
    return " AND ".join(clauses), params


def findings_filter_query(
    run_id: str,
    *,
    severity: str | None,
    check_id: str | None,
    file: str | None,
    category: FindingCategory | None,
    rule_id: str | None = None,
) -> tuple[str, list[object]]:
    where, params = findings_filter_clause(
        run_id,
        severity=severity,
        check_id=check_id,
        file=file,
        category=category,
        rule_id=rule_id,
    )
    return (
        f"SELECT * FROM findings WHERE {where}",  # ruff:ignore[hardcoded-sql-expression]  # nosec B608
        params,
    )


def apply_run_fields(run: RunRecord, updates: dict[str, object | None]) -> None:
    for attr, value in updates.items():
        if value is not None:
            setattr(run, attr, value)


def mark_run_finished(run: RunRecord) -> None:
    finished_at = utc_now()
    run.finished_at = finished_at
    run.duration_ms = int((finished_at - run.started_at).total_seconds() * 1000)


def dt_to_iso(value: datetime) -> str:
    return value.isoformat()


def dt_from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def row_to_run(row: sqlite3.Row) -> RunRecord:
    summary = None
    if row["summary_json"]:
        summary = RunSummaryRecord.from_dict(json.loads(row["summary_json"]))
    return RunRecord(
        id=row["id"],
        branch=row["branch"],
        suite_id=row["suite_id"],
        status=RunStatus(row["status"]),
        started_at=dt_from_iso(row["started_at"]),
        finished_at=(dt_from_iso(row["finished_at"]) if row["finished_at"] else None),
        duration_ms=row["duration_ms"],
        worktree_path=row["worktree_path"],
        error_message=row["error_message"],
        current_check_id=row["current_check_id"],
        checks_completed=row["checks_completed"],
        checks_total=row["checks_total"],
        summary=summary,
    )


def row_to_finding(row: sqlite3.Row) -> FindingRecord:
    keys = set(row.keys())
    category_raw = row["category"] if "category" in keys and row["category"] else "code"
    return FindingRecord(
        id=row["id"],
        run_id=row["run_id"],
        check_id=row["check_id"],
        tool_id=row["tool_id"],
        rule_id=row["rule_id"],
        severity=row["severity"],
        message=row["message"],
        file=row["file"],
        line=row["line"],
        column=row["column_num"],
        docs_url=row["docs_url"],
        suggested_commands=json.loads(row["suggested_commands_json"]),
        category=FindingCategory(category_raw),
    )
