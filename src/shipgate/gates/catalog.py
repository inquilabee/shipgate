"""Gate catalog helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog


def discover_gates(project_root: Path) -> list[Path]:
    gates_dir = project_root / ".shipgate" / "gates"
    if not gates_dir.is_dir():
        return []
    return sorted(p for p in gates_dir.glob("*.sh") if p.is_file())


def merge_gate_catalog(base: Catalog, project_root: Path) -> Catalog:
    """Return base catalog; gate scripts are discovered at runtime."""
    _ = discover_gates(project_root)
    return base
