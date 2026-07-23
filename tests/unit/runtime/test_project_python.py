from pathlib import Path

from tests.unit.support.python_env import PythonEnvFixture

from shipgate.paths import (
    PROJECT_ENV_CACHE_KEY,
    parse_env_file,
    project_root_cache_env_path,
)
from shipgate.project.init import init_project
from shipgate.runtime.project_python import (
    discover_project_python,
    persist_project_python,
    read_cached_project_python,
)


def test_discover_prefers_dot_venv(tmp_path):
    PythonEnvFixture.write_venv(tmp_path / ".venv")

    discovered = discover_project_python(tmp_path)
    assert discovered == Path(".venv")
    cache = parse_env_file(project_root_cache_env_path(tmp_path))
    assert cache[PROJECT_ENV_CACHE_KEY] == ".venv"


def test_discover_ignores_managed_virtual_env(tmp_path, monkeypatch):
    from shipgate.paths import managed_python_env

    managed = managed_python_env(tmp_path)
    PythonEnvFixture.write_venv(managed)
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))

    assert discover_project_python(tmp_path) is None


def test_discover_uses_external_virtual_env(tmp_path, monkeypatch):
    external = tmp_path / "external-venv"
    PythonEnvFixture.write_venv(external)
    monkeypatch.setenv("VIRTUAL_ENV", str(external))

    discovered = discover_project_python(tmp_path)
    assert discovered == Path("external-venv")


def test_read_cached_project_python_uses_saved_path(tmp_path):
    custom = tmp_path / "envs" / "dev"
    PythonEnvFixture.write_venv(custom)
    persist_project_python(tmp_path, custom)

    assert read_cached_project_python(tmp_path) == Path("envs/dev")


def test_init_persists_discovered_project_env(tmp_path):
    PythonEnvFixture.write_venv(tmp_path / ".venv")
    init_project(tmp_path)
    cache = parse_env_file(project_root_cache_env_path(tmp_path))
    assert cache[PROJECT_ENV_CACHE_KEY] == ".venv"


def test_managed_environment_does_not_set_virtual_env(tmp_path, monkeypatch):
    from shipgate.runtime.environment import managed_environment

    parent_venv = tmp_path / "parent-venv"
    monkeypatch.setenv("VIRTUAL_ENV", str(parent_venv))
    env = managed_environment(tmp_path)
    assert "VIRTUAL_ENV" not in env.env
