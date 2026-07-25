from pathlib import Path

from shipgate.domain.reports import CheckReport, RunReport
from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.services.report_access import store_for_run
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.frontend.web.app import create_app
from shipgate.runtime.report_store import ReportStore


def test_store_for_run_uses_worktree_path(tmp_path: Path):
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    storage = SqliteStorage(primary / "report.db")
    run = storage.create_run(branch="feature", suite_id="standard", run_id="run-wt")
    storage.update_run(run.id, worktree_path=str(worktree), status=RunStatus.RUNNING)
    run = storage.get_run(run.id)
    assert run is not None
    store = store_for_run(primary, run)
    assert store.project_root == worktree.resolve()


def test_api_run_and_log_load_from_worktree(tmp_path: Path):
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    (primary / ".shipgate" / "server").mkdir(parents=True)
    storage = SqliteStorage(primary / ".shipgate" / "server" / "report.db")
    run = storage.create_run(branch="feature", suite_id="standard", run_id="abc123def456")
    storage.update_run(
        run.id,
        worktree_path=str(worktree),
        status=RunStatus.SUCCEEDED,
        finished=True,
    )

    log_rel = ".shipgate/reports/runs/abc123def456/stdout.log"
    log_path = worktree / log_rel
    log_path.parent.mkdir(parents=True)
    log_path.write_text("hello-log\n", encoding="utf-8")
    report = RunReport(
        run_id="abc123def456",
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
                stdout_path=log_rel,
            ),
        ),
    )
    ReportStore(worktree).save(report, metadata={"branch": "feature"})

    app = create_app(primary)
    # Avoid startup backfill overwriting; create_app already ran backfill on empty primary store.
    from fastapi.testclient import TestClient

    client = TestClient(app)
    detail = client.get("/api/runs/abc123def456")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == "abc123def456"
    log = client.get("/runs/abc123def456/checks/ruff.lint/log")
    assert log.status_code == 200
    assert "hello-log" in log.text


def test_api_runs_lists_sqlite_not_report_store_only(tmp_path: Path):
    primary = tmp_path / "primary"
    primary.mkdir()
    (primary / ".shipgate" / "server").mkdir(parents=True)
    app = create_app(primary)
    storage: SqliteStorage = app.state.storage
    storage.create_run(branch="main", suite_id="full", run_id="sqliteonly01ab")
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.get("/api/runs")
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["runs"]}
    assert "sqliteonly01ab" in ids
