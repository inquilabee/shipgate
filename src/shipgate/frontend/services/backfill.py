"""Backfill SQLite index from ReportStore history."""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.storage.base import MAX_RUNS
from shipgate.runtime.report_store import ReportStore

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.frontend.storage.sqlite import SqliteStorage


def backfill_from_report_store(project_root: Path, storage: SqliteStorage) -> int:
    """Ingest ReportStore history into SQLite without exceeding MAX_RUNS.

    Skips IDs already present. Does not resurrect pruned history once SQLite
    already holds MAX_RUNS rows (prune and backfill stay coherent).
    Branch comes from report metadata when available — never invents HEAD.
    """
    store = ReportStore(project_root)
    ingested = 0
    for entry in store.list_runs():
        if len(storage.list_runs(limit=MAX_RUNS)) >= MAX_RUNS:
            break
        if ingest_report_store_entry(store, storage, project_root, entry):
            ingested += 1
    return ingested


def ingest_report_store_entry(
    store: ReportStore,
    storage: SqliteStorage,
    project_root: Path,
    entry: dict,
) -> bool:
    run_id = entry.get("run_id")
    if not run_id or storage.has_run(run_id):
        return False
    try:
        report = store.load(run_id)
    except (FileNotFoundError, OSError):
        return False
    branch = str(entry.get("branch") or "unknown")
    suite_id = report.suite or entry.get("suite") or "standard"
    started_at = started_at_from_entry(entry)
    status = RunStatus.SUCCEEDED if report.status == "passed" else RunStatus.FAILED
    storage.create_run(branch=branch, suite_id=suite_id, run_id=run_id)
    # Set started_at before marking finished so duration_ms is honest.
    storage.set_started_at(run_id, started_at)
    summary = ingest_run_report(storage, run_id, report, project_root)
    storage.update_run(
        run_id,
        status=status,
        finished=True,
        summary=summary,
    )
    return True


def started_at_from_entry(entry: dict) -> datetime:
    timestamp = entry.get("timestamp")
    if not timestamp:
        return datetime.now(UTC)
    with contextlib.suppress(ValueError):
        return datetime.fromisoformat(str(timestamp))
    return datetime.now(UTC)
