"""Incremental check helpers."""

from pathlib import Path


def filter_changed(paths: tuple[Path, ...], since: str | None) -> tuple[Path, ...]:
    if since is None:
        return paths
    return paths
