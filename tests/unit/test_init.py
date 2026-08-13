import shutil

from shipgate.cli import main
from shipgate.core import run_command
from shipgate.paths import PROJECT_CACHE_ENV, SHIPGATE_DIR, SHIPGATE_YAML, find_project_root

GIT = shutil.which("git")


def assert_init_layout(root):
    sg = root / SHIPGATE_DIR
    assert (sg / "reports").is_dir(), "reports directory missing"
    assert (sg / "gates").is_dir(), "gates directory missing"
    assert_init_allowlists(sg)
    assert (sg / "configs" / "ruff.toml").is_file(), "ruff config missing"
    gitignore = (sg / ".gitignore").read_text(encoding="utf-8")
    assert "tools/" in gitignore, "tools/ not ignored"
    assert "!configs/" in gitignore, "configs/ not un-ignored"


def assert_init_allowlists(sg) -> None:
    allowlists = sg / "allowlists"
    for name in (
        "acronyms.yaml",
        "module-private-vars.yaml",
        "test-only-symbols.yaml",
        "repeated-strings.yaml",
        "class-local-functions.yaml",
        "staticmethod-soup.yaml",
    ):
        assert (allowlists / name).is_file(), f"{name} allowlist missing"


def assert_default_yaml_policy(content: str) -> None:
    assert "suite: full" in content, "suite not set to full"
    assert "env: managed" in content, "env not managed"
    assert "error-format: compact" in content, "error-format not compact"
    assert "mode: auto" in content, "configs.mode not auto"
    assert "changed-only: true" in content, "changed-only not enabled"
    assert "src/shipgate/frontend/templates/" not in content, (
        "bundled init must not embed shipgate-specific semgrep excludes"
    )
    assert "allowlists:" in content, "allowlists section missing"


def test_init_yaml_writes_layout_scopes(tmp_path, monkeypatch, capsys):
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "src" / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_demo.py").write_text(
        "def test_ok():\n    assert True\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    assert main(["init"]) == 0
    content = (tmp_path / SHIPGATE_YAML).read_text(encoding="utf-8")
    assert "python-src:" in content
    assert "target: src" in content
    assert "python-test-src:" in content
    assert "target: tests" in content
    assert "semgrep:" in content
    captured = capsys.readouterr()
    assert "shipgate check --suite full --full-tree" in captured.out


def test_init_pyproject_writes_layout_scopes(tmp_path, monkeypatch):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "src" / "demo").mkdir(parents=True)
    (tmp_path / "src" / "demo" / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["init", "pyproject"]) == 0
    content = (tmp_path / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.shipgate.scopes.python-src]" in content
    assert 'target = "src"' in content
    assert "src/shipgate/frontend/templates/" not in content


def test_init_creates_shipgate_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    code = main(["init"])
    assert code == 0, "init should succeed"
    config_path = tmp_path / SHIPGATE_YAML
    assert config_path.is_file(), "canonical shipgate.yaml missing"
    assert_default_yaml_policy(config_path.read_text(encoding="utf-8"))
    assert_init_layout(tmp_path)
    assert (tmp_path / "pyproject.toml").is_file(), "yaml init should create minimal pyproject"
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
    run_command([GIT, "init"], cwd=tmp_path, check=True)
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
