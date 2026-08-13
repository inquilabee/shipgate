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
from shipgate.project.layout.packages import detect_importable_root_package


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


def test_project_config_relpath_for_import_linter():
    catalog = CatalogLoader.load()
    tool = catalog.get_tool("import-linter.check")
    assert project_config_relpath(tool) == Path(".shipgate/configs/importlinter.ini")
    assert tool.configuration.bundled == "configs/importlinter.ini"


def test_detect_importable_root_package_from_src_layout(tmp_path: Path):
    pkg = tmp_path / "src" / "acme"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    assert detect_importable_root_package(tmp_path) == "acme"


def test_detect_importable_root_package_from_flat_layout(tmp_path: Path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "service.py").write_text("x = 1\n", encoding="utf-8")
    assert detect_importable_root_package(tmp_path) == "mypkg"


def test_detect_importable_returns_none_without_package(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n", encoding="utf-8")
    assert detect_importable_root_package(tmp_path) is None


def test_detect_importable_ignores_pyproject_only_name(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "cool-pkg"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    assert detect_importable_root_package(tmp_path) is None


def test_scaffold_bundled_configs_creates_files(tmp_path: Path):
    catalog = CatalogLoader.load()
    created = scaffold_bundled_configs(tmp_path, catalog)
    assert (tmp_path / ".shipgate/configs/ruff.toml").is_file(), "ruff config missing"
    assert (tmp_path / ".shipgate/configs/gates/gate.module-size.yaml").is_file(), (
        "gate config missing"
    )
    assert len(created) >= 2, "expected scaffolded files"


def test_scaffold_skips_import_linter_without_package(tmp_path: Path):
    catalog = CatalogLoader.load()
    scaffold_bundled_configs(tmp_path, catalog)
    assert not (tmp_path / ".shipgate/configs/importlinter.ini").is_file()


def test_scaffold_import_linter_substitutes_root_package(tmp_path: Path):
    pkg = tmp_path / "src" / "widgets"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    catalog = CatalogLoader.load()
    scaffold_bundled_configs(tmp_path, catalog)
    content = (tmp_path / ".shipgate/configs/importlinter.ini").read_text(encoding="utf-8")
    assert "root_package = widgets" in content
    assert "__ROOT_PACKAGE__" not in content
    assert "containers =\n    widgets" in content
    assert "(domain)" in content
    assert "widgets.domain" not in content


def test_scaffold_import_linter_flat_layout(tmp_path: Path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "service.py").write_text("x = 1\n", encoding="utf-8")
    catalog = CatalogLoader.load()
    scaffold_bundled_configs(tmp_path, catalog)
    content = (tmp_path / ".shipgate/configs/importlinter.ini").read_text(encoding="utf-8")
    assert "root_package = mypkg" in content


def test_scaffold_does_not_write_deptry_into_pyproject(tmp_path: Path):
    original = '[project]\nname = "demo"\nversion = "0.1.0"\n'
    (tmp_path / "pyproject.toml").write_text(original, encoding="utf-8")
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    catalog = CatalogLoader.load()
    scaffold_bundled_configs(tmp_path, catalog)
    assert (tmp_path / "pyproject.toml").read_text(encoding="utf-8") == original
    assert not (tmp_path / ".mdformat.toml").is_file()
    assert (tmp_path / ".shipgate/configs/mdformat.toml").is_file()


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
    assert not (tmp_path / ".shipgate/configs/importlinter.ini").is_file(), (
        "import-linter should not scaffold without a package"
    )
    assert (tmp_path / "pyproject.toml").is_file(), "yaml init should create minimal pyproject"
    assert (tmp_path / ".shipgate/configs/gates/gate.acronym-allowlist.yaml").is_file(), (
        "gate config missing"
    )


def test_init_scaffolds_import_linter_with_package(tmp_path: Path):
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    init_project(tmp_path)
    assert (tmp_path / ".shipgate/configs/importlinter.ini").is_file()
    content = (tmp_path / ".shipgate/configs/importlinter.ini").read_text(encoding="utf-8")
    assert "root_package = demo" in content


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
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",), (
        "auto mode should use scaffold when no repo-native config exists"
    )


def test_resolve_repo_mode_prefers_shipgate_config(tmp_path: Path):
    from dataclasses import replace

    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    (tmp_path / ".ruff.toml").write_text("[lint]\nselect = ['F']\n", encoding="utf-8")
    project = replace(ProjectConfigLoader.load(project_root=tmp_path), config_mode="repo")
    tool = catalog.get_tool("ruff.lint")
    paths = resolve_config_paths(tool, project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/ruff.toml",), (
        "repo mode should prefer scaffold discover order"
    )


def test_resolve_import_linter_prefers_shipgate_config(tmp_path: Path):
    pkg = tmp_path / "src" / "demo"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    catalog = CatalogLoader.load()
    scaffold_project_layout(tmp_path)
    project = ProjectConfigLoader.load(project_root=tmp_path)
    tool = catalog.get_tool("import-linter.check")
    paths = resolve_config_paths(tool, project, tmp_path)
    assert paths == (tmp_path / ".shipgate/configs/importlinter.ini",)
