from datetime import UTC, datetime, timedelta
from pathlib import Path

from shipgate.domain.reports import CheckReport, RunReport
from shipgate.frontend.services.backfill import backfill_from_report_store
from shipgate.frontend.storage.base import MAX_RUNS
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.runtime.report_store import ReportStore


def test_backfill_uses_metadata_branch_and_honest_duration(tmp_path: Path):
    store = ReportStore(tmp_path)
    started = datetime.now(UTC) - timedelta(seconds=30)
    report = RunReport(
        run_id="backfill01abcd",
        suite="standard",
        mode="check",
        status="passed",
        reports=(
            CheckReport(
                check_id="ruff.lint",
                tool_id="ruff.lint",
                status="passed",
                exit_code=0,
                findings=(),
            ),
        ),
    )
    store.save(
        report,
        metadata={"branch": "feature-x", "timestamp": started.isoformat()},
    )
    storage = SqliteStorage(tmp_path / "report.db")
    assert backfill_from_report_store(tmp_path, storage) == 1
    run = storage.get_run("backfill01abcd")
    assert run is not None
    assert run.branch == "feature-x"
    assert abs((run.started_at - started).total_seconds()) < 1
    assert run.finished_at is not None
    assert run.duration_ms is not None
    # Started 30s ago; duration must reflect that, not ~0 from create_run clock.
    assert run.duration_ms >= 20_000
    assert run.duration_ms < 120_000


def test_backfill_stops_at_max_runs(tmp_path: Path):
    store = ReportStore(tmp_path)
    storage = SqliteStorage(tmp_path / "report.db")
    for index in range(MAX_RUNS):
        storage.create_run(branch="main", suite_id="full", run_id=f"{index:012x}abcd")
    report = RunReport(
        run_id="overflow01abcd",
        suite="standard",
        mode="check",
        status="passed",
        reports=(),
    )
    store.save(report, metadata={"branch": "main"})
    assert backfill_from_report_store(tmp_path, storage) == 0
    assert storage.has_run("overflow01abcd") is False
