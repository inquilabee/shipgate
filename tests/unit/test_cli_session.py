from pathlib import Path
from unittest.mock import MagicMock

import pytest
import typer

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.cli_session import CliRunOptions, CliSession
from shipgate.errors import ShipGateError


def test_build_run_command_maps_options(tmp_path: Path):
    opts = CliRunOptions(suite="full", check="ruff.lint", verbose=True, extra_arg=["--x"])
    command = CliSession.build_run_command(tmp_path, opts)
    assert command == RunCommand(
        project_root=tmp_path,
        suite="full",
        check="ruff.lint",
        verbose=True,
        extra_args=("--x",),
    )


def test_run_rejects_full_tree_with_changed_only(tmp_path: Path, monkeypatch):
    app = MagicMock(spec=ShipGateApp)
    session = CliSession(app=app)
    monkeypatch.setattr("shipgate.cli_session.find_project_root", lambda: tmp_path)

    with pytest.raises(typer.Exit) as exc:
        session.run("check", CliRunOptions(full_tree=True, changed_only=True))
    assert exc.value.exit_code == ShipGateError.exit_code
    app.check.assert_not_called()


def test_run_exits_with_app_code(tmp_path: Path, monkeypatch):
    app = MagicMock(spec=ShipGateApp)
    app.check.return_value = 2
    session = CliSession(app=app)
    monkeypatch.setattr("shipgate.cli_session.find_project_root", lambda: tmp_path)

    with pytest.raises(typer.Exit) as exc:
        session.run("check", CliRunOptions())
    assert exc.value.exit_code == 2
    app.check.assert_called_once()


def test_install_persists_project_env(tmp_path: Path, monkeypatch):
    app = MagicMock(spec=ShipGateApp)
    app.install.return_value = 0
    session = CliSession(app=app)
    custom = tmp_path / "env"
    persisted: list[tuple[Path, Path]] = []

    monkeypatch.setattr("shipgate.cli_session.find_project_root", lambda: tmp_path)
    monkeypatch.setattr(
        "shipgate.cli_session.persist_project_python",
        lambda root, env: persisted.append((root, env)),
    )

    with pytest.raises(typer.Exit) as exc:
        session.install(config=None, suite=None, project_env=custom, verbose=False)
    assert exc.value.exit_code == 0
    assert persisted == [(tmp_path, custom)]
    command = app.install.call_args.args[0]
    assert isinstance(command, InstallCommand)
    assert command.project_root == tmp_path


def test_run_maps_shipgate_error_to_exit(tmp_path: Path, monkeypatch):
    app = MagicMock(spec=ShipGateApp)
    app.check.side_effect = ShipGateError("boom")
    session = CliSession(app=app)
    monkeypatch.setattr("shipgate.cli_session.find_project_root", lambda: tmp_path)

    with pytest.raises(typer.Exit) as exc:
        session.run("check", CliRunOptions())
    assert exc.value.exit_code == ShipGateError.exit_code
