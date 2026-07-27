"""Load the Sourcery rule ID inventory shipped with the refactor package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_INVENTORY_PATH = Path(__file__).resolve().parents[2] / "inventory" / "sourcery_ids.yaml"


@dataclass(frozen=True)
class InventoryEntry:
    id: str
    kind: str
    status: str
    note: str | None = None


def load_inventory(path: Path | None = None) -> list[InventoryEntry]:
    inventory_path = DEFAULT_INVENTORY_PATH if path is None else path
    raw = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        msg = f"inventory must be a YAML list: {inventory_path}"
        raise ValueError(msg)
    return [
        InventoryEntry(
            id=str(entry["id"]),
            kind=str(entry["kind"]),
            status=str(entry["status"]),
            note=entry.get("note"),
        )
        for entry in raw
    ]
