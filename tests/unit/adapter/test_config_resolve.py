"""Tests for bundled config path resolution."""

from dataclasses import replace
from pathlib import Path

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.loader import CatalogLoader
from shipgate.config.loader import ProjectConfigLoader
from shipgate.project.init import scaffold_project_layout


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
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    (tmp_path / ".ruff.toml").write_text("[lint]\nselect = ['F']\n", encoding="utf-8")
    project = replace(ProjectConfigLoader.load(project_root=tmp_path), config_mode="repo")
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",)


def test_auto_mode_prefers_pyproject_over_shipgate_scaffold(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n\n[tool.ruff]\nline-length = 99\n',
        encoding="utf-8",
    )
    project = ProjectConfigLoader.load(project_root=tmp_path)
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / "pyproject.toml",)


def test_auto_mode_uses_shipgate_scaffold_when_only_scaffold_exists(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    project = ProjectConfigLoader.load(project_root=tmp_path)
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",)


def test_auto_mode_prefers_root_ruff_toml_over_shipgate_scaffold(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    (tmp_path / ".ruff.toml").write_text("[lint]\nselect = ['F']\n", encoding="utf-8")
    project = ProjectConfigLoader.load(project_root=tmp_path)
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / ".ruff.toml",)


def test_absolute_discover_pattern_is_ignored(tmp_path: Path):
    catalog = CatalogLoader.load()
    tool = replace(
        catalog.get_tool("ruff.lint"),
        configuration=replace(
            catalog.get_tool("ruff.lint").configuration,
            discover=("/etc/passwd",),
            bundled=None,
        ),
    )
    project = replace(ProjectConfigLoader.load(project_root=tmp_path), config_mode="repo")
    assert resolve_config_paths(tool, project, tmp_path) == ()


def test_parent_discover_pattern_is_ignored(tmp_path: Path):
    project = tmp_path / "proj"
    project.mkdir()
    (tmp_path / "secret.toml").write_text("[lint]\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    tool = replace(
        catalog.get_tool("ruff.lint"),
        configuration=replace(
            catalog.get_tool("ruff.lint").configuration,
            discover=("../secret.toml",),
            bundled=None,
        ),
    )
    project_cfg = replace(ProjectConfigLoader.load(project_root=project), config_mode="repo")
    assert resolve_config_paths(tool, project_cfg, project) == ()


def test_auto_mode_skips_pyproject_without_tool_section(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "demo"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    (tmp_path / ".ruff.toml").write_text("[lint]\nselect = ['F']\n", encoding="utf-8")
    project = ProjectConfigLoader.load(project_root=tmp_path)
    paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    assert paths == (tmp_path / ".ruff.toml",)
