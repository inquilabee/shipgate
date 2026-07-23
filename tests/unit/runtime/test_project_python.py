import sys
from pathlib import Path

from shipgate.paths import managed_python_env
from shipgate.runtime.environment import managed_environment
from shipgate.runtime.project_python import discover_project_python


def test_discover_prefers_dot_venv(tmp_path):
    venv = tmp_path / ".venv"
    if sys.platform == "win32":
        (venv / "Scripts").mkdir(parents=True)
        (venv / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    else:
        (venv / "bin").mkdir(parents=True)
        (venv / "bin" / "python").write_text("", encoding="utf-8")

    discovered = discover_project_python(tmp_path)
    assert discovered == Path(".venv")


def test_discover_ignores_managed_virtual_env(tmp_path, monkeypatch):
    managed = managed_python_env(tmp_path)
    if sys.platform == "win32":
        (managed / "Scripts").mkdir(parents=True)
        (managed / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    else:
        (managed / "bin").mkdir(parents=True)
        (managed / "bin" / "python").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(managed))

    assert discover_project_python(tmp_path) is None


def test_discover_uses_external_virtual_env(tmp_path, monkeypatch):
    external = tmp_path / "external-venv"
    if sys.platform == "win32":
        (external / "Scripts").mkdir(parents=True)
        (external / "Scripts" / "python.exe").write_text("", encoding="utf-8")
    else:
        (external / "bin").mkdir(parents=True)
        (external / "bin" / "python").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIRTUAL_ENV", str(external))

    discovered = discover_project_python(tmp_path)
    assert discovered == external.resolve()


def test_managed_environment_does_not_set_virtual_env(tmp_path, monkeypatch):
    parent_venv = tmp_path / "parent-venv"
    monkeypatch.setenv("VIRTUAL_ENV", str(parent_venv))
    env = managed_environment(tmp_path)
    assert "VIRTUAL_ENV" not in env.env
