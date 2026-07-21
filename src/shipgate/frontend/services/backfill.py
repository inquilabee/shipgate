"""Backfill SQLite index from ReportStore history."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.services.worktree import current_branch
from shipgate.runtime.report_store import ReportStore

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.frontend.storage.sqlite import SqliteStorage


def backfill_from_report_store(project_root: Path, storage: SqliteStorage) -> int:
    store = ReportStore(project_root)
    ingested = 0
    for entry in store.list_runs():
        run_id = entry.get("run_id")
        if not run_id or storage.has_run(run_id):
            continue
        try:
            report = store.load(run_id)
        except (FileNotFoundError, OSError):
            continue
        branch = current_branch(project_root)
        suite_id = report.suite or entry.get("suite") or "standard"
        timestamp = entry.get("timestamp")
        started_at = datetime.now(UTC)
        if timestamp:
            with contextlib.suppress(ValueError):
                started_at = datetime.fromisoformat(str(timestamp))
        status = RunStatus.SUCCEEDED if report.status == "passed" else RunStatus.FAILED
        storage.create_run(branch=branch, suite_id=suite_id, run_id=run_id)
        summary = ingest_run_report(storage, run_id, report, project_root)
        storage.update_run(
            run_id,
            status=status,
            finished=True,
            summary=summary,
        )
        storage.set_started_at(run_id, started_at)
        ingested += 1
    return ingested
