from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.services.ingest import ingest_run_report
from shipgate.frontend.storage.sqlite import SqliteStorage
from shipgate.frontend.web.app import create_app
from shipgate.runtime.report_store import ReportStore

pytest.importorskip("fastapi")


def test_frontend_health_and_overview(tmp_path: Path):
    storage = SqliteStorage(tmp_path / ".shipgate" / "server" / "report.db")
    run = storage.create_run(branch="main", suite_id="standard", run_id="test-run-001")
    report = RunReport(
        run_id="test-run-001",
        suite="standard",
        mode="check",
        status="failed",
        reports=(
            CheckReport(
                check_id="ruff.lint",
                tool_id="ruff.lint",
                status="failed",
                exit_code=1,
                findings=(
                    Finding(
                        check_id="ruff.lint",
                        rule_id="F401",
                        severity="error",
                        message="unused import",
                        location=FindingLocation(path="src/app.py", line=3),
                    ),
                ),
            ),
        ),
    )
    summary = ingest_run_report(storage, run.id, report, tmp_path)
    storage.update_run(run.id, status=RunStatus.FAILED, finished=True, summary=summary)
    ReportStore(tmp_path).save(report)

    client = TestClient(create_app(tmp_path))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"ok": True}

    overview = client.get("/")
    assert overview.status_code == 200
    assert "Overview" in overview.text

    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert any(r.get("run_id") == "test-run-001" for r in runs.json()["runs"])

    detail = client.get("/api/runs/test-run-001")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == "test-run-001"

    findings_page = client.get("/runs/test-run-001/findings")
    assert findings_page.status_code == 200
    assert "unused import" in findings_page.text

    summary_api = client.get("/api/runs/test-run-001/summary")
    assert summary_api.status_code == 200
    assert summary_api.json()["finding_count"] == 1

    findings_api = client.get("/api/runs/test-run-001/findings")
    assert findings_api.status_code == 200
    assert findings_api.json()["total"] == 1

    tools = client.get("/tools")
    assert tools.status_code == 200
    assert "ruff.lint" in tools.text

    static = client.get("/static/css/app.css")
    assert static.status_code == 200
