"""SQLite schema DDL and migrations for the report server."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    branch TEXT NOT NULL,
    suite_id TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    duration_ms INTEGER,
    worktree_path TEXT,
    error_message TEXT,
    current_check_id TEXT,
    checks_completed INTEGER NOT NULL DEFAULT 0,
    checks_total INTEGER NOT NULL DEFAULT 0,
    summary_json TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    check_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    file TEXT,
    line INTEGER,
    column_num INTEGER,
    docs_url TEXT,
    suggested_commands_json TEXT NOT NULL DEFAULT '[]',
    category TEXT NOT NULL DEFAULT 'code',
    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_started_at ON runs(started_at);
CREATE INDEX IF NOT EXISTS idx_runs_branch ON runs(branch);
CREATE INDEX IF NOT EXISTS idx_findings_run_id ON findings(run_id);
"""


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(findings)").fetchall()}
    if "category" not in columns:
        conn.execute(
            "ALTER TABLE findings ADD COLUMN category TEXT NOT NULL DEFAULT 'code'"
        )
