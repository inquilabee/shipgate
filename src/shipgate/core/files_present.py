"""Glob-based presence checks for catalog suggest_if / require_if."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def any_files_present(root: Path, patterns: tuple[str, ...]) -> bool:
    """Return True when any glob pattern matches under ``root``."""
    return any(any(root.glob(pattern)) for pattern in patterns)
