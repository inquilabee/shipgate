"""Tests for bundled config path resolution."""

from pathlib import Path

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.loader import CatalogLoader
from shipgate.config.loader import ProjectConfigLoader


def test_resolve_bundled_config_per_tool(tmp_path: Path):
    catalog = CatalogLoader.load()
    project = ProjectConfigLoader.load(project_root=tmp_path)

    ruff_paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    yamllint_paths = resolve_config_paths(catalog.get_tool("yamllint.check"), project, tmp_path)

    assert ruff_paths
    assert yamllint_paths
    assert ruff_paths != yamllint_paths
    assert ruff_paths[0].name == "ruff.toml"
    assert yamllint_paths[0].name == "yamllint.yaml"
    assert "catalog/bundled" in str(ruff_paths[0])


def test_resolve_repo_mode_uses_shipgate_first(tmp_path: Path):
    from dataclasses import replace

    from shipgate.project.init import scaffold_project_layout

    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    project = replace(ProjectConfigLoader.load(project_root=tmp_path), config_mode="repo")
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",)
