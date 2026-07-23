"""Path-based gate allowlists with documented reasons per entry."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from shipgate.core.yaml_io import load_yaml_mapping


@dataclass(frozen=True)
class PathAllowlistEntry:
    path: str
    reason: str


class PathAllowlistLoader:
    @staticmethod
    def load_entries(path: Path) -> tuple[PathAllowlistEntry, ...]:
        if not path.is_file():
            return ()
        raw = load_yaml_mapping(
            path,
            error_cls=ValueError,
            invalid_message=f"path allowlist must be YAML: {path}",
        )
        return PathAllowlistLoader._parse_entries(raw.get("entries", []), path)

    @staticmethod
    def _parse_entries(entries_raw: object, path: Path) -> tuple[PathAllowlistEntry, ...]:
        if entries_raw is None:
            entries_raw = []
        if not isinstance(entries_raw, list):
            msg = f"path allowlist entries must be a list: {path}"
            raise ValueError(msg)
        return tuple(
            PathAllowlistLoader._parse_entry(item, index, path)
            for index, item in enumerate(entries_raw)
        )

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

    @staticmethod
    def load_paths(path: Path) -> set[str]:
        return {entry.path for entry in PathAllowlistLoader.load_entries(path)}

    @staticmethod
    def contains(rel_path: str, allowlist_path: Path) -> bool:
        normalized = rel_path.rstrip("/")
        return normalized in PathAllowlistLoader.load_paths(allowlist_path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Query a path-based YAML allowlist.")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--contains", required=True)
    args = parser.parse_args(argv)
    if PathAllowlistLoader.contains(args.contains, args.file):
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
