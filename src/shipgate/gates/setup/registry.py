"""Gate-owned project setup registry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from shipgate.gates.setup.acronym_allowlist import setup as setup_acronym_allowlist
from shipgate.gates.setup.folder_breadth import setup as setup_folder_breadth
from shipgate.gates.setup.module_private_vars import setup as setup_module_private_vars
from shipgate.gates.setup.module_size import setup as setup_module_size

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from shipgate.domain.catalog import Catalog


class GateSetup(Protocol):
    def setup(self, project_root: Path) -> None: ...


SETUPS: dict[str, Callable[[Path], None]] = {
    "gate.module-size": setup_module_size,
    "gate.module-private-vars": setup_module_private_vars,
    "gate.folder-breadth": setup_folder_breadth,
    "gate.acronym-allowlist": setup_acronym_allowlist,
}


def setup_bundled_gates(project_root: Path, catalog: Catalog) -> None:
    """Run per-gate setup for bundled policy gates that register scaffolding."""
    for tool_id, setup in SETUPS.items():
        if not catalog.is_tool(tool_id):
            continue
        setup(project_root.resolve())
