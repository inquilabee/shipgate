from shipgate.cli import main
from shipgate.paths import PROJECT_CACHE_ENV, PROJECT_ENV_CACHE_KEY, parse_env_file
from shipgate.project.init import init_project
from tests.unit.support.python_env import PythonEnvFixture


def test_project_env_flag_persists_to_cache(tmp_path, monkeypatch):
    custom = tmp_path / "pyenv"
    PythonEnvFixture(custom).write()
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    monkeypatch.setattr("shipgate.app.ShipGateApp.install", lambda _self, _command: 0)

    code = main(["install", "--project-env", str(custom)])
    assert code == 0

    cache = parse_env_file(tmp_path / PROJECT_CACHE_ENV)
    assert cache[PROJECT_ENV_CACHE_KEY] == "pyenv"
