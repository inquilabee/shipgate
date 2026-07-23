"""Scope path helpers for script gates."""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.domain.execution import ResolvedRequest


def scope_paths_from_env() -> tuple[str, ...]:
    raw = os.environ.get("SHIPGATE_SCOPE_PATHS", "")
    return tuple(line.strip() for line in raw.splitlines() if line.strip())


def gate_scope_paths(resolved: ResolvedRequest) -> tuple[str, ...]:
    delivery = resolved.tool.scope.delivery
    paths: list[str] = []
    for path in resolved.options.paths:
        rel_str = gate_scope_rel_path(resolved, path)
        if rel_str is None:
            continue
        candidate = path if path.is_absolute() else resolved.project_root / path
        scoped = gate_scope_entry(delivery, candidate, rel_str)
        if scoped is not None:
            paths.append(scoped)
    return tuple(dict.fromkeys(paths))


def gate_scope_rel_path(resolved: ResolvedRequest, path: Path) -> str | None:
    if not path.parts:
        return None
    if not path.is_absolute():
        return str(path).replace("\\", "/")
    try:
        rel = path.relative_to(resolved.project_root)
    except ValueError:
        return None
    return str(rel).replace("\\", "/")


def gate_scope_entry(delivery: str, candidate: Path, rel_str: str) -> str | None:
    if delivery == "files":
        return rel_str if candidate.is_file() else None
    if delivery in {"dirs", "root"}:
        return directory_delivery_scope_entry(delivery, candidate, rel_str)
    return None


def directory_delivery_scope_entry(delivery: str, candidate: Path, rel_str: str) -> str | None:
    if candidate.is_dir() or rel_str in {".", ""}:
        return rel_str or "."
    if candidate.is_file():
        parent = Path(rel_str).parent
        return "." if not parent.parts else str(parent).replace("\\", "/")
    if delivery == "root":
        # Planned/incremental paths may not exist on disk yet.
        return rel_str or "."
    return None
