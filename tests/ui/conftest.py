"""Playwright UI fixtures: ephemeral server + FakeOrchestrator."""

from __future__ import annotations

import socket
import threading
from typing import TYPE_CHECKING

import pytest
import uvicorn

from shipgate.frontend.web.app import create_app
from tests.frontend.support.seed import prepare_frontend_root, seed_failed_run
from tests.ui.support.fake_orchestrator import FakeOrchestrator

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

pytest.importorskip("playwright")
pytestmark = pytest.mark.ui


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def ui_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("SHIPGATE_UI_TEST", "1")
    return prepare_frontend_root(tmp_path)


@pytest.fixture
def ui_app(ui_root: Path):
    seed_failed_run(ui_root, with_baseline=True)
    app = create_app(ui_root)
    app.state.orchestrator = FakeOrchestrator(ui_root, app.state.storage, step_delay=0.2)
    return app


@pytest.fixture
def cancel_ui_app(ui_root: Path):
    """App whose fake runs stay RUNNING until cancelled."""
    seed_failed_run(ui_root, with_baseline=True)
    app = create_app(ui_root)
    app.state.orchestrator = FakeOrchestrator(
        ui_root,
        app.state.storage,
        step_delay=0.2,
        auto_complete=False,
    )
    return app


@pytest.fixture
def live_server(ui_app) -> Iterator[str]:
    port = free_port()
    config = uvicorn.Config(ui_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        threading.Event().wait(0.05)
    assert server.started, "uvicorn failed to start"
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture
def cancel_live_server(cancel_ui_app) -> Iterator[str]:
    port = free_port()
    config = uvicorn.Config(cancel_ui_app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(50):
        if server.started:
            break
        threading.Event().wait(0.05)
    assert server.started, "uvicorn failed to start"
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
