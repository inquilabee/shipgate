"""Tests for project config scaffolding."""

from pathlib import Path

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.loader import load_catalog
from shipgate.config.loader import load_config
from shipgate.project.config_setup import project_config_relpath, scaffold_bundled_configs
from shipgate.project.init import init_project, scaffold_project_layout


def test_project_config_relpath_deduplicates_ruff():
    catalog = load_catalog()
    ruff_lint = catalog.get_tool("ruff.lint")
    ruff_format = catalog.get_tool("ruff.format")
    assert project_config_relpath(ruff_lint) == Path(".shipgate/configs/ruff.toml")
    assert project_config_relpath(ruff_format) == project_config_relpath(ruff_lint)


def test_project_config_relpath_for_gate():
    catalog = load_catalog()
    tool = catalog.get_tool("gate.module-size")
    assert project_config_relpath(tool) == Path(".shipgate/configs/gates/gate.module-size.yaml")


def test_scaffold_bundled_configs_creates_files(tmp_path: Path):
    catalog = load_catalog()
    created = scaffold_bundled_configs(tmp_path, catalog)
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file()
    assert (tmp_path / ".shipgate/configs/gates/gate.module-size.yaml").is_file()
    assert len(created) >= 2


def test_scaffold_bundled_configs_does_not_overwrite(tmp_path: Path):
    catalog = load_catalog()
    path = tmp_path / ".shipgate/configs/ruff.toml"
    path.parent.mkdir(parents=True)
    path.write_text("custom = true\n", encoding="utf-8")
    created = scaffold_bundled_configs(tmp_path, catalog)
    assert path.read_text(encoding="utf-8") == "custom = true\n"
    assert path not in created


def test_init_scaffolds_configs(tmp_path: Path):
    init_project(tmp_path)
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file()
    assert (tmp_path / ".shipgate/configs/ty.toml").is_file()
    assert (tmp_path / ".shipgate/configs/gates/gate.acronym-allowlist.yaml").is_file()


def test_init_shipgate_yaml_enables_changed_only(tmp_path: Path):
    init_project(tmp_path)
    project = load_config(project_root=tmp_path)
    assert project.changed_only is True


def test_init_configs_only_without_shipgate_yaml(tmp_path: Path):
    init_project(tmp_path, configs_only=True)
    assert not (tmp_path / "shipgate.yaml").is_file()
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file()


def test_resolve_prefers_shipgate_config(tmp_path: Path):
    catalog = load_catalog()
    scaffold_project_layout(tmp_path)
    project = load_config(project_root=tmp_path)
    tool = catalog.get_tool("ruff.lint")
    paths = resolve_config_paths(tool, project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",)
