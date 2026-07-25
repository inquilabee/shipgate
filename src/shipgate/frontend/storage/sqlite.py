"""SQLite implementation of the report-server Storage protocol."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from typing import TYPE_CHECKING

from shipgate.frontend.domain.models import (
    FindingCategory,
    FindingRecord,
    RunRecord,
    RunStatus,
    RunSummaryRecord,
)
from shipgate.frontend.storage import mapping
from shipgate.frontend.storage.base import MAX_RUNS
from shipgate.frontend.storage.schema import init_schema

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime
    from pathlib import Path

COMPLETED_STATUSES = (
    RunStatus.SUCCEEDED.value,
    RunStatus.FAILED.value,
    RunStatus.CANCELLED.value,
)


class SqliteStorage:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            init_schema(conn)

    def create_run(
        self,
        *,
        branch: str,
        suite_id: str,
        worktree_path: str | None = None,
        run_id: str | None = None,
    ) -> RunRecord:
        run = RunRecord(
            id=run_id or uuid.uuid4().hex,
            branch=branch,
            suite_id=suite_id,
            status=RunStatus.QUEUED,
            started_at=mapping.utc_now(),
            worktree_path=worktree_path,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    id, branch, suite_id, status, started_at, finished_at, duration_ms,
                    worktree_path, error_message, current_check_id,
                    checks_completed, checks_total, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.id,
                    run.branch,
                    run.suite_id,
                    run.status.value,
                    mapping.dt_to_iso(run.started_at),
                    None,
                    None,
                    run.worktree_path,
                    None,
                    None,
                    run.checks_completed,
                    run.checks_total,
                    None,
                ),
            )
        return run

    def has_run(self, run_id: str) -> bool:
        return self.get_run(run_id) is not None

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return mapping.row_to_run(row)

    def list_runs(self, *, limit: int = 50, branch: str | None = None) -> list[RunRecord]:
        query = "SELECT * FROM runs"
        params: list[object] = []
        if branch is not None:
            query += " WHERE branch = ?"
            params.append(branch)
        query += " ORDER BY started_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [mapping.row_to_run(row) for row in rows]

    def update_run(
        self,
        run_id: str,
        *,
        status: RunStatus | None = None,
        worktree_path: str | None = None,
        error_message: str | None = None,
        current_check_id: str | None = None,
        checks_completed: int | None = None,
        checks_total: int | None = None,
        finished: bool = False,
        summary: RunSummaryRecord | None = None,
    ) -> RunRecord:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(f"run not found: {run_id}")
        mapping.apply_run_fields(
            run,
            {
                "status": status,
                "worktree_path": worktree_path,
                "error_message": error_message,
                "current_check_id": current_check_id,
                "checks_completed": checks_completed,
                "checks_total": checks_total,
                "summary": summary,
            },
        )
        if finished:
            mapping.mark_run_finished(run)
        self._persist_run(run, run_id)
        return run

    def _persist_run(self, run: RunRecord, run_id: str) -> None:
        summary_json = None if run.summary is None else json.dumps(run.summary.to_dict())
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE runs SET
                    status = ?,
                    finished_at = ?,
                    duration_ms = ?,
                    worktree_path = ?,
                    error_message = ?,
                    current_check_id = ?,
                    checks_completed = ?,
                    checks_total = ?,
                    summary_json = ?
                WHERE id = ?
                """,
                (
                    run.status.value,
                    mapping.dt_to_iso(run.finished_at) if run.finished_at else None,
                    run.duration_ms,
                    run.worktree_path,
                    run.error_message,
                    run.current_check_id,
                    run.checks_completed,
                    run.checks_total,
                    summary_json,
                    run_id,
                ),
            )

    def replace_findings(self, run_id: str, findings: list[FindingRecord]) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM findings WHERE run_id = ?", (run_id,))
            conn.executemany(
                """
                INSERT INTO findings (
                    id, run_id, check_id, tool_id, rule_id, severity, message,
                    file, line, column_num, docs_url, suggested_commands_json, category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        f.id,
                        f.run_id,
                        f.check_id,
                        f.tool_id,
                        f.rule_id,
                        f.severity,
                        f.message,
                        f.file,
                        f.line,
                        f.column,
                        f.docs_url,
                        json.dumps(f.suggested_commands),
                        f.category.value,
                    )
                    for f in findings
                ],
            )

    def list_findings(
        self,
        run_id: str,
        *,
        severity: str | None = None,
        check_id: str | None = None,
        file: str | None = None,
        category: FindingCategory | None = None,
        rule_id: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[FindingRecord]:
        query, params = mapping.findings_filter_query(
            run_id,
            severity=severity,
            check_id=check_id,
            file=file,
            category=category,
            rule_id=rule_id,
        )
        query += " ORDER BY file, line, id"
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [mapping.row_to_finding(row) for row in rows]

    def count_findings(
        self,
        run_id: str,
        *,
        severity: str | None = None,
        check_id: str | None = None,
        file: str | None = None,
        category: FindingCategory | None = None,
        rule_id: str | None = None,
    ) -> int:
        where, params = mapping.findings_filter_clause(
            run_id,
            severity=severity,
            check_id=check_id,
            file=file,
            category=category,
            rule_id=rule_id,
        )
        # where/params come from findings_filter_clause (column allowlist), not user SQL.
        query = f"SELECT COUNT(*) FROM findings WHERE {where}"  # ruff:ignore[hardcoded-sql-expression]  # nosec B608
        with self._connect() as conn:
            row = conn.execute(query, params).fetchone()
        return int(row[0])

    def upsert_check_findings(
        self, run_id: str, check_id: str, findings: list[FindingRecord]
    ) -> None:
        existing = [f for f in self.list_findings(run_id) if f.check_id != check_id]
        self.replace_findings(run_id, existing + list(findings))

    def set_started_at(self, run_id: str, started_at: datetime) -> None:
        run = self.get_run(run_id)
        if run is None:
            raise KeyError(f"run not found: {run_id}")
        run.started_at = started_at
        duration_ms = run.duration_ms
        if run.finished_at is not None:
            duration_ms = int((run.finished_at - started_at).total_seconds() * 1000)
            run.duration_ms = duration_ms
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET started_at = ?, duration_ms = ? WHERE id = ?",
                (mapping.dt_to_iso(started_at), duration_ms, run_id),
            )

    def previous_completed_run(self, *, branch: str, before_run_id: str) -> RunRecord | None:
        before = self.get_run(before_run_id)
        if before is None:
            return None
        placeholders = ", ".join("?" for _ in COMPLETED_STATUSES)
        query = (
            f"SELECT * FROM runs WHERE branch = ? AND status IN ({placeholders}) "  # ruff:ignore[hardcoded-sql-expression]  # nosec B608
            "AND started_at < ? ORDER BY started_at DESC LIMIT 1"
        )
        with self._connect() as conn:
            row = conn.execute(
                query,
                (branch, *COMPLETED_STATUSES, mapping.dt_to_iso(before.started_at)),
            ).fetchone()
        if row is None:
            return None
        return mapping.row_to_run(row)

    def prune_old_runs(self, keep: int = MAX_RUNS) -> int:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
            if total <= keep:
                return 0
            to_delete = total - keep
            rows = conn.execute(
                """
                SELECT id FROM runs
                ORDER BY started_at ASC
                LIMIT ?
                """,
                (to_delete,),
            ).fetchall()
            ids = [row["id"] for row in rows]
            if not ids:
                return 0
            placeholders = ", ".join("?" for _ in ids)
            conn.execute(f"DELETE FROM findings WHERE run_id IN ({placeholders})", ids)  # ruff:ignore[hardcoded-sql-expression]  # nosec B608
            conn.execute(f"DELETE FROM runs WHERE id IN ({placeholders})", ids)  # ruff:ignore[hardcoded-sql-expression]  # nosec B608
            return len(ids)
