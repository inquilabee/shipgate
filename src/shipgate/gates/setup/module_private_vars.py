"""Setup for gate.module-private-vars."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import load_catalog
from shipgate.gates.config import load_bundled_gate_config
from shipgate.gates.setup.scaffold import scaffold_from_gate_config

if TYPE_CHECKING:
    from pathlib import Path


def setup(project_root: Path) -> None:
    tool = load_catalog().get_tool("gate.module-private-vars")
    scaffold_from_gate_config(
        project_root,
        load_bundled_gate_config(tool),
    )
