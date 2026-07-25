from pathlib import Path

from shipgate import __version__, load_catalog
from shipgate.app import RunCommand, ShipGateApp
from shipgate.runtime.executor import Executor, ProcessResult


class FakeExecutor(Executor):
    def run(self, argv, *, cwd, env=None):  # ruff:ignore[no-self-use]
        _ = env
        return ProcessResult(
            argv=argv,
            cwd=cwd,
            exit_code=0,
            stdout="[]",
            stderr="",
            duration_ms=1,
        )


def test_public_api_load_catalog():
    catalog = load_catalog()
    assert "ruff.lint" in catalog.tools


def test_public_api_run(tmp_path: Path):
    app = ShipGateApp(catalog=load_catalog(), executor=FakeExecutor())
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=tmp_path,
            quiet=True,
        )
    )
    assert code == 0


def test_version_exported():
    assert __version__ == "0.1.2"
