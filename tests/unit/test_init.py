import shutil
import subprocess

from shipgate.cli import main
from shipgate.paths import PROJECT_CACHE_ENV, SHIPGATE_DIR, SHIPGATE_YAML, find_project_root

GIT = shutil.which("git")


def assert_init_layout(root):
    sg = root / SHIPGATE_DIR
    assert (sg / "reports").is_dir(), "reports directory missing"
    assert (sg / "gates").is_dir(), "gates directory missing"
    assert (sg / "allowlists" / "acronyms.yaml").is_file(), "acronyms allowlist missing"
    assert (sg / "allowlists" / "module-private-vars.yaml").is_file(), (
        "module-private-vars allowlist missing"
    )
    assert (sg / "configs" / "ruff.toml").is_file(), "ruff config missing"
    gitignore = (sg / ".gitignore").read_text(encoding="utf-8")
    assert "tools/" in gitignore, "tools/ not ignored"
    assert "!configs/" in gitignore, "configs/ not un-ignored"


def test_init_creates_shipgate_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["init"])
    assert code == 0, "init should succeed"
    config_path = tmp_path / SHIPGATE_YAML
    assert config_path.is_file(), "canonical shipgate.yaml missing"
    content = config_path.read_text(encoding="utf-8")
    assert "suite: full" in content, "suite not set to full"
    assert "env: managed" in content, "env not managed"
    assert "error-format: compact" in content, "error-format not compact"
    assert "mode: auto" in content, "configs.mode not auto"
    assert "changed-only: true" in content, "changed-only not enabled"
    assert "allowlists:" in content, "allowlists section missing"
    assert_init_layout(tmp_path)
    cache = (tmp_path / PROJECT_CACHE_ENV).read_text(encoding="utf-8")
    assert "SHIPGATE_POLICY=yaml" in cache, "yaml policy not cached"


def test_init_yaml_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["init", "yaml"])
    assert code == 0, "init yaml should succeed"
    assert (tmp_path / SHIPGATE_YAML).is_file(), "canonical shipgate.yaml missing"


def test_init_pyproject_subcommand(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    code = main(["init", "pyproject"])
    assert code == 0, "init pyproject should succeed"
    assert "[tool.shipgate]" in (tmp_path / "pyproject.toml").read_text(encoding="utf-8"), (
        "tool.shipgate section missing"
    )
    assert not (tmp_path / SHIPGATE_YAML).is_file(), "yaml policy should not be created"
    cache = (tmp_path / PROJECT_CACHE_ENV).read_text(encoding="utf-8")
    assert "SHIPGATE_POLICY=pyproject" in cache, "pyproject policy not cached"


def test_init_refuses_existing_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / SHIPGATE_YAML
    config_path.parent.mkdir(parents=True)
    config_path.write_text("suite: full\n", encoding="utf-8")
    code = main(["init"])
    assert code != 0, "init should refuse existing config"


def test_find_project_root_prefers_shipgate_yaml(tmp_path):
    if GIT is None:
        return
    subprocess.run([GIT, "init"], cwd=tmp_path, check=True, capture_output=True)
    nested = tmp_path / "nested"
    nested.mkdir()
    config_path = tmp_path / SHIPGATE_YAML
    config_path.parent.mkdir(parents=True)
    config_path.write_text("suite: standard\n", encoding="utf-8")
    assert find_project_root(nested) == tmp_path.resolve(), "canonical yaml should win"


def test_find_project_root_uses_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    nested = tmp_path / "pkg"
    nested.mkdir()
    assert find_project_root(nested) == tmp_path.resolve(), "pyproject should anchor root"
