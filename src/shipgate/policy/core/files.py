"""Shared file discovery for policy gates."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.gates.scope_paths import scope_paths_from_env

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.gates.ignore import EffectiveIgnores


def path_is_allowlisted(rel: str, allowlist: set[str]) -> bool:
    """True when rel matches an allowlist path or sits under an allowlisted directory."""
    cleaned = rel.rstrip("/")
    if cleaned in allowlist:
        return True
    parts = cleaned.split("/")
    return any("/".join(parts[:index]) in allowlist for index in range(1, len(parts)))


def symbol_is_allowlisted(rel: str, symbol: str, allowlist: set[str]) -> bool:
    cleaned = rel.rstrip("/")
    return True if path_is_allowlisted(cleaned, allowlist) else f"{cleaned}:{symbol}" in allowlist


def should_skip_file(rel: str, allowlist: set[str], ignores: EffectiveIgnores | None) -> bool:
    return (
        True
        if path_is_allowlisted(rel, allowlist)
        else (ignores.is_ignored(rel) if ignores is not None else False)
    )


def iter_python_files(root: Path, scan_roots: tuple[str, ...]) -> list[str]:
    if scoped := scope_paths_from_env():
        return list(scoped)
    files: list[str] = []
    for scan_root in scan_roots:
        base = root / scan_root
        if not base.is_dir():
            continue
        files.extend(
            path.relative_to(root).as_posix()
            for path in sorted(base.rglob("*.py"))
            if path.is_file()
        )
    return files


def scan_roots_from_config(config: dict[str, object]) -> tuple[str, ...]:
    raw = config.get("scan_roots", ["."])
    return tuple(str(item) for item in raw) if isinstance(raw, list | tuple) else (".",)
