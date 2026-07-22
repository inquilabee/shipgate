import shutil
import subprocess

import pytest
from shipgate.cli import main
from shipgate.paths import find_project_root, shipgate_dir

GIT = shutil.which("git")


def test_init_creates_shipgate_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["init"])
    assert code == 0
    config_path = tmp_path / "shipgate.yaml"
    assert config_path.is_file()
    content = config_path.read_text(encoding="utf-8")
    assert "suite: standard" in content
    assert "error-format: compact" in content
    assert "mode: auto" in content
    assert (shipgate_dir(tmp_path) / "reports").is_dir()
    assert (shipgate_dir(tmp_path) / "gates").is_dir()
    assert (shipgate_dir(tmp_path) / "allowlists" / "acronyms.yaml").is_file()
    assert (shipgate_dir(tmp_path) / "allowlists" / "module-private-vars.txt").is_file()


def test_init_refuses_existing_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "shipgate.yaml").write_text("suite: full\n", encoding="utf-8")
    code = main(["init"])
    assert code != 0


@pytest.mark.skipif(GIT is None, reason="git not on PATH")
def test_find_project_root_prefers_shipgate_yaml(tmp_path):
    assert GIT is not None
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "shipgate.yaml").write_text("suite: standard\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve()


def test_find_project_root_uses_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    nested = tmp_path / "pkg"
    nested.mkdir()
    assert find_project_root(nested) == tmp_path.resolve()
