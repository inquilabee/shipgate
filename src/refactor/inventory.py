"""Load the rule ID inventory shipped with the refactor package."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from refactor.protocol import ApplyMode

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

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
    packs: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()
    delegates_to: str | None = None


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
        packs=parse_str_tuple(mapping.get("packs")),
        tags=parse_str_tuple(mapping.get("tags")),
        delegates_to=optional_str(mapping.get("delegates_to")),
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


def parse_str_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    msg = f"expected string list, got {value!r}"
    raise TypeError(msg)


def optional_str(value: object) -> str | None:
    return None if value is None else str(value)


def inventory_by_id(
    inventory: Sequence[InventoryEntry] | None = None,
) -> dict[str, InventoryEntry]:
    entries = load_inventory() if inventory is None else inventory
    return {entry.id: entry for entry in entries}


def enable_tokens_for(entry: InventoryEntry) -> frozenset[str]:
    return frozenset({*entry.packs, *entry.tags})


def entry_enabled_by(
    entry: InventoryEntry,
    enable: Iterable[str],
) -> bool:
    """Core rules (no packs) are always selected; pack rules need a token match."""
    if not entry.packs:
        return True
    wanted = frozenset(enable)
    return not enable_tokens_for(entry).isdisjoint(wanted)


def rule_pack_selected(
    rule_id: str,
    enable: Iterable[str],
    *,
    inventory: Mapping[str, InventoryEntry] | None = None,
) -> bool:
    entries = inventory if inventory is not None else inventory_by_id()
    entry = entries.get(rule_id)
    return True if entry is None else entry_enabled_by(entry, enable)


def parse_enable_tokens(values: Sequence[str] | None) -> frozenset[str]:
    if not values:
        return frozenset()
    tokens: set[str] = set()
    for value in values:
        tokens |= {part.strip() for part in value.split(",") if part.strip()}
    return frozenset(tokens)
