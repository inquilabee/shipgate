"""Tests for project config scaffolding."""

from pathlib import Path

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.loader import CatalogLoader
from shipgate.config.loader import ProjectConfigLoader
from shipgate.paths import SHIPGATE_YAML
from shipgate.project.config_setup import (
    project_config_relpath,
    scaffold_bundled_configs,
)
from shipgate.project.init import init_project, scaffold_project_layout


def test_project_config_relpath_deduplicates_ruff():
    catalog = CatalogLoader.load()
    ruff_lint = catalog.get_tool("ruff.lint")
    ruff_format = catalog.get_tool("ruff.format")
    assert project_config_relpath(ruff_lint) == Path(".shipgate/configs/ruff.toml"), (
        "ruff.lint config path mismatch"
    )
    assert project_config_relpath(ruff_format) == project_config_relpath(ruff_lint), (
        "ruff.format should share ruff.toml"
    )


def test_project_config_relpath_for_gate():
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("gate.module-size")
    assert project_config_relpath(tool) == Path(".shipgate/configs/gates/gate.module-size.yaml"), (
        "gate config path mismatch"
    )


def test_scaffold_bundled_configs_creates_files(tmp_path: Path):
    catalog = CatalogLoader.load()
    created = scaffold_bundled_configs(tmp_path, catalog)
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file(), "ruff config missing"
    assert (tmp_path / ".shipgate/configs/gates/gate.module-size.yaml").is_file(), (
        "gate config missing"
    )
    assert len(created) >= 2, "expected scaffolded files"


def test_scaffold_bundled_configs_does_not_overwrite(tmp_path: Path):
    catalog = CatalogLoader.load()
    path = tmp_path / ".shipgate/configs/ruff.toml"
    path.parent.mkdir(parents=True)
    path.write_text("custom = true\n", encoding="utf-8")
    created = scaffold_bundled_configs(tmp_path, catalog)
    assert path.read_text(encoding="utf-8") == "custom = true\n", "existing config overwritten"
    assert path not in created, "unchanged file should not be listed"


def test_init_scaffolds_configs(tmp_path: Path):
    init_project(tmp_path)
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file(), "ruff config missing"
    assert (tmp_path / ".shipgate/configs/ty.toml").is_file(), "ty config missing"
    assert (tmp_path / ".shipgate/configs/gates/gate.acronym-allowlist.yaml").is_file(), (
        "gate config missing"
    )


def test_init_shipgate_yaml_enables_changed_only(tmp_path: Path):
    init_project(tmp_path)
    project = ProjectConfigLoader.load(project_root=tmp_path)
    assert project.changed_only is True, "changed-only should default true"


def test_init_configs_only_without_shipgate_yaml(tmp_path: Path):
    init_project(tmp_path, configs_only=True)
    assert not (tmp_path / SHIPGATE_YAML).is_file(), "policy file should not be created"
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file(), "configs should be scaffolded"


def test_resolve_prefers_shipgate_config(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    project = ProjectConfigLoader.load(project_root=tmp_path)
    tool = catalog.get_tool("ruff.lint")
    paths = resolve_config_paths(tool, project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",), "project config not preferred"
