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


def make_setup(gate_id: str, catalog: Catalog | None = None) -> Callable[[Path], None]:
    def setup(project_root: Path) -> None:
        tool = (catalog or CatalogLoader.load()).get_tool(gate_id)
        scaffold_from_gate_config(
            project_root,
            load_bundled_gate_config(tool),
        )

    return setup


GATE_SETUP_IDS: frozenset[str] = frozenset(
    {
        "gate.module-size",
        "gate.module-private-vars",
        "gate.folder-breadth",
        "gate.acronym-allowlist",
        "gate.test-only-symbols",
        "gate.repeated-strings",
        "gate.class-local-functions",
        "gate.staticmethod-soup",
    }
)


def setup_bundled_gates(project_root: Path, catalog: Catalog) -> None:
    """Run per-gate setup for bundled policy gates that register scaffolding."""
    for tool_id in GATE_SETUP_IDS:
        if not catalog.is_tool(tool_id):
            continue
        make_setup(tool_id, catalog)(project_root.resolve())
