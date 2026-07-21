"""Lockfile management."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

LOCKFILE_SCHEMA = "shipgate.lock.v1"


def write_lockfile(path: Path, packages: dict[str, str]) -> None:
    data = {"schema_version": LOCKFILE_SCHEMA, "packages": packages}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def read_lockfile(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return dict(data.get("packages", {}))
