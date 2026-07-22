"""Tests for project catalog sync and loader precedence."""

from pathlib import Path

from shipgate.app import ShipGateApp
from shipgate.catalog.loader import load_catalog, merge_catalog_raw
from shipgate.project.catalog import sync_catalog
from shipgate.project.init import init_project, scaffold_project_layout


def test_sync_catalog_creates_missing_files(tmp_path: Path):
    created = sync_catalog(tmp_path)
    assert (tmp_path / ".shipgate/catalog/tools/ruff.lint.yaml").is_file()
    assert (tmp_path / ".shipgate/catalog/suites.yaml").is_file()
    assert (tmp_path / ".shipgate/catalog/workflows.yaml").is_file()
    assert (tmp_path / ".shipgate/catalog/capabilities.yaml").is_file()
    assert len(created) >= 4


def test_sync_catalog_does_not_overwrite(tmp_path: Path):
    path = tmp_path / ".shipgate/catalog/suites.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("suites:\n  custom:\n    members: []\n", encoding="utf-8")
    created = sync_catalog(tmp_path)
    assert path.read_text(encoding="utf-8").startswith("suites:\n  custom:")
    assert path not in created


def test_load_catalog_project_overrides_bundled(tmp_path: Path):
    sync_catalog(tmp_path)
    tool_path = tmp_path / ".shipgate/catalog/tools/ruff.lint.yaml"
    tool_path.write_text(
        "ruff.lint:\n  executable: custom-ruff\n  modes:\n    - check\n",
        encoding="utf-8",
    )
    catalog = load_catalog(project_root=tmp_path)
    assert catalog.get_tool("ruff.lint").executable == "custom-ruff"


def test_load_catalog_falls_back_to_bundled_without_project_catalog(tmp_path: Path):
    catalog = load_catalog(project_root=tmp_path)
    assert catalog.get_tool("ruff.lint").executable == "ruff"


def test_merge_catalog_raw_overlay_wins():
    base = {"tools": {"a": {"id": "a"}}, "suites": {"standard": {"members": ["a"]}}}
    overlay = {"tools": {"b": {"id": "b"}}, "suites": {"custom": {"members": ["b"]}}}
    merged = merge_catalog_raw(base, overlay)
    assert "a" in merged["tools"]
    assert "b" in merged["tools"]
    assert "standard" in merged["suites"]
    assert "custom" in merged["suites"]


def test_init_scaffolds_catalog(tmp_path: Path):
    init_project(tmp_path)
    assert (tmp_path / ".shipgate/catalog/tools/ruff.lint.yaml").is_file()
    assert (tmp_path / ".shipgate/catalog/suites.yaml").is_file()


def test_scaffold_project_layout_includes_catalog(tmp_path: Path):
    created = scaffold_project_layout(tmp_path)
    assert any(path.name == "ruff.lint.yaml" for path in created)


def test_app_catalog_for_uses_project_catalog(tmp_path: Path):
    sync_catalog(tmp_path)
    tool_path = tmp_path / ".shipgate/catalog/tools/ruff.lint.yaml"
    tool_path.write_text(
        "ruff.lint:\n  executable: project-ruff\n  modes:\n    - check\n",
        encoding="utf-8",
    )
    app = ShipGateApp()
    catalog = app._catalog_for(tmp_path)
    assert catalog.get_tool("ruff.lint").executable == "project-ruff"
