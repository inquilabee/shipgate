"""Tests for bundled config path resolution."""

from pathlib import Path

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.catalog.loader import load_catalog
from shipgate.config.loader import load_config


def test_resolve_bundled_config_per_tool(tmp_path: Path):
    catalog = load_catalog()
    project = load_config(project_root=tmp_path)

    ruff_paths = resolve_config_paths(catalog.get_tool("ruff.lint"), project, tmp_path)
    yamllint_paths = resolve_config_paths(catalog.get_tool("yamllint.check"), project, tmp_path)

    assert ruff_paths
    assert yamllint_paths
    assert ruff_paths != yamllint_paths
    assert ruff_paths[0].name == "ruff.toml"
    assert yamllint_paths[0].name == "yamllint.yaml"
