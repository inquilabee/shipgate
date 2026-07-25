from datetime import UTC, datetime

from shipgate.domain.reports import CheckReport, RunReport
from shipgate.frontend.domain.models import RunRecord, RunStatus, RunSummaryRecord
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.frontend.web.context.overview import gate_status


def test_gate_status_failed_when_gate_check_failed_with_zero_findings(tmp_path):
    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="full", run_id="run-1")
    report = RunReport(
        run_id="run-1",
        suite="full",
        mode="check",
        status="failed",
        reports=(
            CheckReport(
                check_id="gate.python_gates",
                tool_id="gate.python_gates",
                status="failed",
                exit_code=1,
                findings=(),
            ),
        ),
    )
    summary = ingest_run_report(storage, "run-1", report, tmp_path)
    assert summary.by_check_status["gate.python_gates"] == "failed"
    assert summary.by_check_id["gate.python_gates"] == 0
    run = RunRecord(
        id="run-1",
        branch="main",
        suite_id="full",
        status=RunStatus.FAILED,
        started_at=datetime.now(UTC),
        summary=summary,
    )
    assert gate_status(run) == "failed"


def test_gate_status_passed_when_gate_checks_passed():
    run = RunRecord(
        id="run-1",
        branch="main",
        suite_id="full",
        status=RunStatus.SUCCEEDED,
        started_at=datetime.now(UTC),
        summary=RunSummaryRecord(
            finding_count=0,
            by_check_id={"gate.python_gates": 0},
            by_check_status={"gate.python_gates": "passed"},
        ),
    )
    assert gate_status(run) == "passed"


def test_ingest_records_by_check_status(tmp_path):
    storage = SqliteStorage(tmp_path / "report.db")
    storage.create_run(branch="main", suite_id="standard", run_id="run-1")
    report = RunReport(
        run_id="run-1",
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
    summary = ingest_run_report(storage, "run-1", report, tmp_path)
    assert summary.by_check_status == {"ruff.lint": "passed"}
