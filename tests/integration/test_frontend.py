from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from tests.frontend.support.seed import DEFAULT_RUN_ID, make_seeded_client

if TYPE_CHECKING:
    from pathlib import Path

pytest.importorskip("fastapi")


def test_frontend_health(tmp_path: Path):
    client = make_seeded_client(tmp_path)
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"ok": True}


def test_frontend_overview_pages(tmp_path: Path):
    client = make_seeded_client(tmp_path)
    overview = client.get("/")
    assert overview.status_code == 200
    assert "Overview" in overview.text

    findings_page = client.get(f"/runs/{DEFAULT_RUN_ID}/findings")
    assert findings_page.status_code == 200
    assert "unused import" in findings_page.text

    tools = client.get("/tools")
    assert tools.status_code == 200
    assert "ruff.lint" in tools.text

    static = client.get("/static/css/app.css")
    assert static.status_code == 200


def test_frontend_api_routes(tmp_path: Path):
    client = make_seeded_client(tmp_path)

    runs = client.get("/api/runs")
    assert runs.status_code == 200
    assert any(r.get("id") == DEFAULT_RUN_ID for r in runs.json()["runs"])

    detail = client.get(f"/api/runs/{DEFAULT_RUN_ID}")
    assert detail.status_code == 200
    assert detail.json()["run_id"] == DEFAULT_RUN_ID

    summary_api = client.get(f"/api/runs/{DEFAULT_RUN_ID}/summary")
    assert summary_api.status_code == 200
    assert summary_api.json()["finding_count"] == 2

    findings_api = client.get(f"/api/runs/{DEFAULT_RUN_ID}/findings")
    assert findings_api.status_code == 200
    assert findings_api.json()["total"] == 2
