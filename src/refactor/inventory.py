"""Load the rule ID inventory shipped with the refactor package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from refactor.protocol import ApplyMode

DEFAULT_INVENTORY_PATH = Path(__file__).resolve().parent / "inventory" / "rule_ids.yaml"


@dataclass(frozen=True)
class InventoryEntry:
    id: str
    kind: str
    status: str
    apply_mode: ApplyMode = ApplyMode.HINT
    note: str | None = None
    rationale: str | None = None
    example_bad: str | None = None
    example_good: str | None = None


def load_inventory(path: Path | None = None) -> list[InventoryEntry]:
    inventory_path = DEFAULT_INVENTORY_PATH if path is None else path
    raw = yaml.safe_load(inventory_path.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        msg = f"inventory must be a YAML list: {inventory_path}"
        raise ValueError(msg)
    return [parse_inventory_entry(entry) for entry in raw]


def parse_inventory_entry(entry: object) -> InventoryEntry:
    if not isinstance(entry, dict):
        msg = f"inventory entry must be a mapping: {entry!r}"
        raise ValueError(msg)
    mapping = {str(key): value for key, value in entry.items()}
    return InventoryEntry(
        id=str(mapping["id"]),
        kind=str(mapping["kind"]),
        status=str(mapping["status"]),
        apply_mode=parse_apply_mode(mapping),
        note=optional_str(mapping.get("note")),
        rationale=optional_str(mapping.get("rationale")),
        example_bad=optional_str(mapping.get("example_bad")),
        example_good=optional_str(mapping.get("example_good")),
    )


def parse_apply_mode(entry: dict[str, object]) -> ApplyMode:
    match entry.get("apply_mode"):
        case None:
            # Migration alias: legacy ``safe_apply: true`` → auto.
            return ApplyMode.AUTO if entry.get("safe_apply") is True else ApplyMode.HINT
        case bool() as flag:
            # YAML 1.1 may parse bare ``off``/``on`` as booleans.
            return ApplyMode.AUTO if flag else ApplyMode.OFF
        case value:
            return ApplyMode(str(value))


def optional_str(value: object) -> str | None:
    return None if value is None else str(value)
