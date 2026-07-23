from argparse import Namespace

from shipgate.app import ShipGateApp
from shipgate.cli import build_parser, dispatch_command
from shipgate.paths import PROJECT_ENV_CACHE_KEY, parse_env_file, project_root_cache_env_path
from shipgate.project.init import init_project
from tests.unit.support.python_env import PythonEnvFixture


def test_project_env_flag_persists_to_cache(tmp_path, monkeypatch):
    custom = tmp_path / "pyenv"
    PythonEnvFixture.write_venv(custom)
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    monkeypatch.setattr(ShipGateApp, "install", lambda self, command: 0)

    args = Namespace(
        command="install",
        config=None,
        suite=None,
        project_env=custom,
    )
    dispatch_command(ShipGateApp(), args, build_parser(), tmp_path)

    cache = parse_env_file(project_root_cache_env_path(tmp_path))
    assert cache[PROJECT_ENV_CACHE_KEY] == "pyenv"
