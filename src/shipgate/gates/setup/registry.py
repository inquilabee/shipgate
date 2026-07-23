"""Gate-owned project setup registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import CatalogLoader
from shipgate.gates.config import load_bundled_gate_config
from shipgate.gates.setup.scaffold import scaffold_from_gate_config

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog


def make_setup(gate_id: str) -> Callable[[Path], None]:
    def setup(project_root: Path) -> None:
        tool = CatalogLoader.load().get_tool(gate_id)
        scaffold_from_gate_config(
            project_root,
            load_bundled_gate_config(tool),
        )

    return setup


SETUPS: dict[str, Callable[[Path], None]] = {
    gate_id: make_setup(gate_id)
    for gate_id in (
        "gate.module-size",
        "gate.module-private-vars",
        "gate.folder-breadth",
        "gate.acronym-allowlist",
    )
}


def setup_bundled_gates(project_root: Path, catalog: Catalog) -> None:
    """Run per-gate setup for bundled policy gates that register scaffolding."""
    for tool_id, setup in SETUPS.items():
        if not catalog.is_tool(tool_id):
            continue
        setup(project_root.resolve())
