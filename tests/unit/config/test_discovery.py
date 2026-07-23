from pathlib import Path

from shipgate.config.discovery import discover_yaml_config_path
from shipgate.config.loader import ProjectConfigLoader
from shipgate.paths import SHIPGATE_YAML, find_project_root


def write_yaml(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def shipgate_yaml_path(project_root: Path) -> Path:
    return project_root / SHIPGATE_YAML


def test_discover_prefers_shipgate_dir_yaml(tmp_path: Path):
    write_yaml(shipgate_yaml_path(tmp_path), "suite: canonical\n")
    write_yaml(tmp_path / "shipgate.yaml", "suite: legacy\n")
    assert discover_yaml_config_path(tmp_path) == shipgate_yaml_path(tmp_path).resolve()


def test_discover_legacy_root_yaml(tmp_path: Path):
    write_yaml(tmp_path / "shipgate.yaml", "suite: legacy\n")
    assert discover_yaml_config_path(tmp_path) == (tmp_path / "shipgate.yaml").resolve()


def test_discover_legacy_dot_yaml(tmp_path: Path):
    write_yaml(tmp_path / ".shipgate.yaml", "suite: hidden\n")
    assert discover_yaml_config_path(tmp_path) == (tmp_path / ".shipgate.yaml").resolve()


def test_canonical_yaml_loads(tmp_path: Path):
    write_yaml(shipgate_yaml_path(tmp_path), "suite: python-quality\n")
    config = ProjectConfigLoader.load(project_root=tmp_path)
    assert config.suite == "python-quality"


def test_find_project_root_prefers_shipgate_dir_yaml(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    write_yaml(shipgate_yaml_path(tmp_path), "suite: standard\n")
    assert find_project_root(nested) == tmp_path.resolve()
