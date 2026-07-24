"""Path-based gate allowlists with documented reasons per entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.core.yaml_io import load_yaml_mapping

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class PathAllowlistEntry:
    path: str
    reason: str


class PathAllowlist:
    """Loaded YAML path allowlist for one file."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries = self._load(path)
        self._paths = frozenset(entry.path for entry in self._entries)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def entries(self) -> tuple[PathAllowlistEntry, ...]:
        return self._entries

    def paths(self) -> frozenset[str]:
        return self._paths

    def contains(self, rel_path: str) -> bool:
        return rel_path.rstrip("/") in self._paths

    def _load(self, path: Path) -> tuple[PathAllowlistEntry, ...]:
        if not path.is_file():
            return ()
        raw = load_yaml_mapping(
            path,
            error_cls=ValueError,
            invalid_message=f"path allowlist must be YAML: {path}",
        )
        return self._parse_entries(raw.get("entries", []), path)

    def _parse_entries(self, entries_raw: object, path: Path) -> tuple[PathAllowlistEntry, ...]:
        if entries_raw is None:
            entries_raw = []
        if not isinstance(entries_raw, list):
            msg = f"path allowlist entries must be a list: {path}"
            raise ValueError(msg)
        return tuple(self._parse_entry(item, index, path) for index, item in enumerate(entries_raw))

    @staticmethod
    def _parse_entry(item: object, index: int, path: Path) -> PathAllowlistEntry:
        if not isinstance(item, dict):
            msg = f"path allowlist entry {index} must be a mapping: {path}"
            raise ValueError(msg)
        entry_path = item.get("path")
        reason = item.get("reason")
        if not entry_path or not isinstance(entry_path, str):
            msg = f"path allowlist entry {index} requires path: {path}"
            raise ValueError(msg)
        if not reason or not isinstance(reason, str) or not reason.strip():
            msg = f"path allowlist entry {index} requires reason: {path}"
            raise ValueError(msg)
        return PathAllowlistEntry(path=entry_path.strip().rstrip("/"), reason=reason.strip())
