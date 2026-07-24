"""Shared file discovery for policy gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.gates.scope_paths import scope_paths_from_env

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores


def should_skip_file(rel: str, allowlist: set[str], ignores: EffectiveIgnores | None) -> bool:
    if rel.rstrip("/") in allowlist:
        return True
    return bool(ignores and ignores.is_ignored(rel))


def iter_python_files(root: Path, scan_roots: tuple[str, ...]) -> list[str]:
    scoped = scope_paths_from_env()
    if scoped:
        return list(scoped)
    files: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.py")):
            if path.is_file():
                files.append(path.relative_to(root).as_posix())
    return files


def scan_roots_from_config(config: dict[str, object]) -> tuple[str, ...]:
    raw = config.get("scan_roots", ["."])
    if not isinstance(raw, list | tuple):
        return (".",)
    return tuple(str(item) for item in raw)
