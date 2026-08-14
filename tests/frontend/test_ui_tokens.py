from pathlib import Path

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

from shipgate.frontend.web.app import contained_file, create_app
from shipgate.frontend.web.security import (
    UI_SESSION_COOKIE,
    is_loopback_host,
    require_bind_safety,
    validate_run_submit_tokens,
    warn_if_non_loopback,
)


def csrf_from_html(text: str) -> str:
    start = text.index('name="csrf_token"')
    value_idx = text.index('value="', start) + len('value="')
    end = text.index('"', value_idx)
    return text[value_idx:end]


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
            ui_token_expected="expected",  # ruff:ignore[hardcoded-password-func-arg]
            ui_token_submitted=None,
        )


def test_require_ui_token_blocks_get_without_unlock(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path, require_ui_token=True))
    response = client.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 403
    api = client.get("/api/runs")
    assert api.status_code == 403
    health = client.get("/health")
    assert health.status_code == 200


def test_new_run_rejects_missing_token_when_configured(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path, require_ui_token=True))
    page = client.get("/ui-token")
    assert page.status_code == 200
    assert "expected" not in page.text
    csrf = csrf_from_html(page.text)
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


def test_new_run_accepts_ui_session_cookie_after_unlock(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path, require_ui_token=True))
    unlock_page = client.get("/ui-token")
    assert unlock_page.status_code == 200
    assert "expected" not in unlock_page.text
    unlock_csrf = csrf_from_html(unlock_page.text)
    unlock = client.post(
        "/ui-token",
        data={"csrf_token": unlock_csrf, "token": "expected"},
        follow_redirects=False,
    )
    assert unlock.status_code == 303
    session_cookie = unlock.cookies.get(UI_SESSION_COOKIE)
    assert session_cookie
    assert session_cookie != "expected"
    page = client.get("/runs/new")
    assert page.status_code == 200
    assert "expected" not in page.text
    csrf = csrf_from_html(page.text)
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
    assert response.status_code != 403


def test_ui_token_mismatch_redirects_with_error(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path, require_ui_token=True))
    unlock_page = client.get("/ui-token")
    unlock_csrf = csrf_from_html(unlock_page.text)
    unlock = client.post(
        "/ui-token",
        data={"csrf_token": unlock_csrf, "token": "wrong"},
        follow_redirects=False,
    )
    assert unlock.status_code == 303
    assert "error=" in unlock.headers["location"]


def test_new_run_accepts_ui_token_header(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("SHIPGATE_UI_TOKEN", "expected")
    client = TestClient(create_app(tmp_path, require_ui_token=True))
    page = client.get("/ui-token")
    csrf = csrf_from_html(page.text)
    response = client.post(
        "/runs/new",
        data={
            "branch": "main",
            "suite_id": "standard",
            "csrf_token": csrf,
            "acknowledge_requirements": "1",
        },
        headers={"X-ShipGate-UI-Token": "expected"},
        follow_redirects=False,
    )
    assert response.status_code != 403


def test_resolved_log_path_rejects_traversal(tmp_path: Path):
    root = tmp_path / "wt"
    root.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("nope", encoding="utf-8")
    with pytest.raises(ValueError, match="path escapes root"):
        contained_file(root, "../secret.txt")


def test_contained_file_returns_existing_file(tmp_path: Path):
    root = tmp_path / "wt"
    root.mkdir()
    log = root / "out.txt"
    log.write_text("ok\n", encoding="utf-8")
    assert contained_file(root, "out.txt") == log.resolve()


def test_serve_warns_on_non_loopback_host(capsys):
    warn_if_non_loopback("0.0.0.0")  # ruff:ignore[hardcoded-bind-all-interfaces]
    assert "0.0.0.0" in capsys.readouterr().err  # ruff:ignore[hardcoded-bind-all-interfaces]


def test_require_bind_safety_exits_without_token(monkeypatch):
    monkeypatch.delenv("SHIPGATE_UI_TOKEN", raising=False)
    with pytest.raises(SystemExit, match="SHIPGATE_UI_TOKEN"):
        require_bind_safety("0.0.0.0")  # ruff:ignore[hardcoded-bind-all-interfaces]


def test_bracketed_ipv6_loopback_is_loopback():
    assert is_loopback_host("[::1]")
    assert is_loopback_host("::1")
    assert is_loopback_host("127.0.0.1")


def test_require_bind_safety_allows_bracketed_ipv6_loopback(monkeypatch):
    monkeypatch.delenv("SHIPGATE_UI_TOKEN", raising=False)
    require_bind_safety("[::1]")


def test_require_safe_branch_rejects_dashed_names():
    from shipgate.frontend.services.worktree import WorktreeError, WorktreeManager

    with pytest.raises(WorktreeError, match="invalid branch"):
        WorktreeManager.require_safe_branch("--help")
    with pytest.raises(WorktreeError, match="invalid branch"):
        WorktreeManager.require_safe_branch("")
