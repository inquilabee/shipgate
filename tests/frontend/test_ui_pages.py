"""Broad TestClient coverage for report UI HTML and JSON routes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.web.app import create_app
from tests.frontend.support.seed import (
    DEFAULT_RUN_ID,
    prepare_frontend_root,
    seed_failed_run,
)

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.frontend.storage.sqlite import SqliteStorage


def test_overview_has_gate_charts_and_log_links(seeded_client: TestClient):
    page = seeded_client.get("/")
    assert page.status_code == 200
    assert "Quality gate: failed" in page.text
    assert "data-charts" in page.text
    assert 'id="chart-severity"' in page.text
    assert f"/runs/{DEFAULT_RUN_ID}/checks/" in page.text
    assert "stdout" in page.text


def test_overview_new_fixed_link_with_baseline(seeded_client_with_baseline: TestClient):
    page = seeded_client_with_baseline.get("/")
    assert page.status_code == 200
    assert f"/runs/{DEFAULT_RUN_ID}/new-code" in page.text
    assert "fixed" in page.text.lower()


def test_findings_rule_filter_html(seeded_client: TestClient):
    all_findings = seeded_client.get(f"/runs/{DEFAULT_RUN_ID}/findings")
    assert all_findings.status_code == 200
    assert "unused import" in all_findings.text
    assert "line too long" in all_findings.text
    assert 'name="rule_id"' in all_findings.text

    filtered = seeded_client.get(f"/runs/{DEFAULT_RUN_ID}/findings?rule_id=F401")
    assert filtered.status_code == 200
    assert "unused import" in filtered.text
    assert "line too long" not in filtered.text


def test_findings_rule_filter_api(seeded_client: TestClient):
    api = seeded_client.get(f"/api/runs/{DEFAULT_RUN_ID}/findings?rule_id=E501")
    assert api.status_code == 200
    body = api.json()
    assert body["total"] == 1
    assert body["findings"][0]["rule_id"] == "E501"
    assert body["findings"][0].get("docs_url") is None

    f401 = seeded_client.get(f"/api/runs/{DEFAULT_RUN_ID}/findings?rule_id=F401")
    assert f401.json()["findings"][0]["docs_url"]


def test_new_run_form_fields(seeded_client: TestClient):
    page = seeded_client.get("/runs/new")
    assert page.status_code == 200
    assert 'name="check"' in page.text
    assert 'name="changed_only"' in page.text
    assert 'name="since"' in page.text
    assert 'name="csrf_token"' in page.text
    assert "Entire suite" in page.text


def test_new_code_page(seeded_client_with_baseline: TestClient):
    page = seeded_client_with_baseline.get(f"/runs/{DEFAULT_RUN_ID}/new-code")
    assert page.status_code == 200
    assert "New / Fixed" in page.text
    assert "unused variable" in page.text or "Fixed" in page.text


def test_new_code_page_without_baseline(seeded_client: TestClient):
    page = seeded_client.get(f"/runs/{DEFAULT_RUN_ID}/new-code")
    assert page.status_code == 200
    assert "No project baseline" in page.text


def test_progress_partial_running_and_install(tmp_path: Path):
    prepare_frontend_root(tmp_path)
    client = TestClient(create_app(tmp_path))
    storage: SqliteStorage = client.app.state.storage
    running = storage.create_run(branch="main", suite_id="standard", run_id="prog-run-0001")
    storage.update_run(
        running.id,
        status=RunStatus.RUNNING,
        checks_completed=0,
        checks_total=0,
    )
    installing = storage.create_run(branch="main", suite_id="standard", run_id="prog-run-0002")
    storage.update_run(
        installing.id,
        status=RunStatus.RUNNING,
        checks_completed=1,
        checks_total=3,
        current_check_id="ruff.lint",
    )
    install_page = client.get(f"/partials/runs/{running.id}/progress")
    assert install_page.status_code == 200
    assert "Installing" in install_page.text
    assert 'action="/runs/' in install_page.text
    assert "cancel" in install_page.text

    progress = client.get(f"/partials/runs/{installing.id}/progress")
    assert progress.status_code == 200
    assert "ruff.lint" in progress.text
    assert "checks 1/3" in progress.text


def test_tools_page_shows_catalog_display_fields(seeded_client: TestClient):
    page = seeded_client.get("/tools")
    assert page.status_code == 200
    assert "Ruff Lint" in page.text or "ruff.lint" in page.text
    assert "Bandit" in page.text or "bandit.scan" in page.text


def test_api_overview_and_trends(seeded_client: TestClient):
    overview = seeded_client.get(f"/api/runs/{DEFAULT_RUN_ID}/overview")
    assert overview.status_code == 200
    payload = overview.json()
    assert payload["run_id"] == DEFAULT_RUN_ID
    assert payload["finding_count"] == 2
    assert payload["gate_status"] == "failed"

    trends = seeded_client.get("/api/runs/trends?branch=main")
    assert trends.status_code == 200
    assert any(row["run_id"] == DEFAULT_RUN_ID for row in trends.json()["runs"])


def test_overview_payload_helpers(tmp_path: Path):
    from shipgate.domain.reports import CheckReport, Finding, FindingLocation, RunReport
    from shipgate.frontend.services.ingest import ingest_run_report
    from shipgate.frontend.web.context.overview import overview_payload, trends_payload

    primary = tmp_path / "primary"
    primary.mkdir()
    (primary / ".shipgate" / "server").mkdir(parents=True)
    app = create_app(primary)
    storage: SqliteStorage = app.state.storage
    run = storage.create_run(branch="main", suite_id="full", run_id="overview01abcd")
    report = RunReport(
        run_id=run.id,
        suite="full",
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
                        message="unused",
                        location=FindingLocation(path="a.py", line=1),
                    ),
                ),
            ),
        ),
    )
    summary = ingest_run_report(storage, run.id, report, primary)
    storage.update_run(run.id, status=RunStatus.FAILED, finished=True, summary=summary)

    payload = overview_payload(storage, primary, run.id)
    assert payload is not None
    assert payload["finding_count"] == 1
    assert payload["by_severity"]["error"] == 1
    assert trends_payload(storage, branch="main", limit=5)
    assert client_status(app, f"/api/runs/{run.id}/overview") == 200
    assert client_status(app, "/api/runs/trends?branch=main") == 200
    assert client_status(app, f"/runs/{run.id}/new-code") == 200


def client_status(app, path: str) -> int:
    return TestClient(app).get(path).status_code


def test_cancel_rejects_bad_csrf(tmp_path: Path):
    seed_failed_run(tmp_path)
    client = TestClient(create_app(tmp_path))
    storage: SqliteStorage = client.app.state.storage
    run = storage.create_run(branch="main", suite_id="full", run_id="cancelme00001")
    storage.update_run(
        run.id,
        status=RunStatus.RUNNING,
        checks_total=2,
        checks_completed=0,
    )
    response = client.post(
        f"/runs/{run.id}/cancel",
        data={"csrf_token": "not-the-token"},
        follow_redirects=False,
    )
    assert response.status_code == 403


def test_new_run_rejects_bad_csrf(seeded_client: TestClient):
    response = seeded_client.post(
        "/runs/new",
        data={
            "branch": "main",
            "suite_id": "standard",
            "csrf_token": "bad",
            "acknowledge_requirements": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 403
