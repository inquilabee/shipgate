"""Project initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import load_catalog
from shipgate.errors import ShipGateError
from shipgate.gates.setup import setup_bundled_gates
from shipgate.paths import shipgate_dir

if TYPE_CHECKING:
    from pathlib import Path

INIT_TEMPLATE = """\
suite: standard
error-format: compact
configs:
  mode: auto
"""


def init_project(project_root: Path) -> Path:
    """Create shipgate.yaml and .shipgate/ scaffolding at the project root."""
    root = project_root.resolve()
    config_path = root / "shipgate.yaml"
    if config_path.is_file():
        raise ShipGateError(f"shipgate.yaml already exists: {config_path}")
    config_path.write_text(INIT_TEMPLATE, encoding="utf-8")
    (shipgate_dir(root) / "reports").mkdir(parents=True, exist_ok=True)
    (shipgate_dir(root) / "gates").mkdir(parents=True, exist_ok=True)
    setup_bundled_gates(root, load_catalog())
    return config_path
