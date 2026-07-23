from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

from shipgate.frontend.web.app import create_app
from shipgate.frontend.web.security import validate_run_submit_tokens


def test_validate_run_submit_tokens_requires_csrf():
    with pytest.raises(PermissionError):
        validate_run_submit_tokens(
            csrf_expected="abc",
            csrf_submitted=None,
            ui_token_expected=None,
            ui_token_submitted=None,
        )


def test_validate_run_submit_tokens_requires_ui_token_when_set():
    with pytest.raises(PermissionError):
        validate_run_submit_tokens(
            csrf_expected="abc",
            csrf_submitted="abc",
            ui_token_expected="expected",  # noqa: S106
            ui_token_submitted=None,
        )


def test_new_run_rejects_missing_token_when_configured(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path))
    page = client.get("/runs/new")
    assert page.status_code == 200
    csrf = page.context.get("csrf_token") if hasattr(page, "context") else None
    # Parse CSRF from HTML hidden field.
    assert 'name="csrf_token"' in page.text
    start = page.text.index('name="csrf_token"')
    value_idx = page.text.index('value="', start) + len('value="')
    end = page.text.index('"', value_idx)
    csrf = page.text[value_idx:end]
    response = client.post(
        "/runs/new",
        data={
            "branch": "main",
            "suite_id": "standard",
            "csrf_token": csrf,
            "acknowledge_requirements": "1",
        },
        follow_redirects=False,
    )
    assert response.status_code == 403
