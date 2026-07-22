"""Project initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import load_catalog
from shipgate.errors import ShipGateError
from shipgate.gates.setup import setup_bundled_gates
from shipgate.paths import shipgate_dir
from shipgate.project.config_setup import scaffold_bundled_configs

if TYPE_CHECKING:
    from pathlib import Path

INIT_TEMPLATE = """\
suite: standard
env: managed
error-format: compact
configs:
  mode: auto
"""


def scaffold_project_layout(project_root: Path) -> list[Path]:
    """Create .shipgate/ directories and copy missing bundled configs."""
    root = project_root.resolve()
    catalog = load_catalog()
    (shipgate_dir(root) / "reports").mkdir(parents=True, exist_ok=True)
    (shipgate_dir(root) / "gates").mkdir(parents=True, exist_ok=True)
    (shipgate_dir(root) / "configs").mkdir(parents=True, exist_ok=True)
    created = scaffold_bundled_configs(root, catalog)
    setup_bundled_gates(root, catalog)
    return created


def init_project(project_root: Path, *, configs_only: bool = False) -> Path | None:
    """Create shipgate.yaml and .shipgate/ scaffolding at the project root."""
    root = project_root.resolve()
    config_path = root / "shipgate.yaml"
    if configs_only:
        scaffold_project_layout(root)
        return None
    if config_path.is_file():
        raise ShipGateError(f"shipgate.yaml already exists: {config_path}")
    config_path.write_text(INIT_TEMPLATE, encoding="utf-8")
    scaffold_project_layout(root)
    return config_path
