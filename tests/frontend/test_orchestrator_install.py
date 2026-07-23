"""Run orchestrator installs into the run worktree root."""

from pathlib import Path
from unittest.mock import MagicMock

from shipgate.frontend.domain.models import RunStatus
from shipgate.frontend.services.orchestrator import RunOrchestrator


def test_perform_run_installs_into_worktree(tmp_path: Path, monkeypatch):
    primary = tmp_path / "primary"
    worktree = tmp_path / "worktree"
    primary.mkdir()
    worktree.mkdir()
    installed: list[Path] = []

    storage = MagicMock()
    storage.list_runs.return_value = []
    storage.create_run.return_value = MagicMock(id="run-1")
    app = MagicMock()
    app._catalog_for.return_value = object()
    app.run_suite.return_value = (0, MagicMock(status="passed", reports=()))

    orch = RunOrchestrator(primary, storage, app=app)
    monkeypatch.setattr(orch, "_resolve_worktree", lambda _branch: worktree)

    def fake_install(root, suite_id, catalog):
        installed.append(Path(root))
        return root / "manifest.json"

    monkeypatch.setattr(
        "shipgate.frontend.services.orchestrator.install_suite",
        fake_install,
    )
    monkeypatch.setattr(
        "shipgate.frontend.services.orchestrator.ingest_run_report",
        lambda *_args, **_kwargs: None,
    )

    orch._perform_run("run-1", "feature", "standard")
    assert installed == [worktree]
    storage.update_run.assert_any_call(
        "run-1",
        status=RunStatus.RUNNING,
        worktree_path=str(worktree),
    )
    command = app.run_suite.call_args.args[0]
    assert command.project_root == worktree
