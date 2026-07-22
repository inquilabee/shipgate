"""Incremental check helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def filter_changed(
    paths: tuple[Path, ...],
    since: str | None,
    *,
    project_root: Path,
    changed_only: bool = False,
) -> tuple[Path, ...]:
    if not changed_only and since is None:
        return paths
    ref = since or "HEAD"
    changed = _git_changed_files(project_root, ref)
    if not changed:
        return ()
    filtered = tuple(path for path in paths if _path_matches_changed(path, project_root, changed))
    if changed_only:
        return filtered
    return filtered or paths


def _git_executable() -> str:
    git = shutil.which("git")
    if git is None:
        return "git"
    return git


def _git_changed_files(project_root: Path, since: str) -> set[str]:
    if not (project_root / ".git").exists():
        return set()
    git = _git_executable()
    result = subprocess.run(  # noqa: S603
        [git, "diff", "--name-only", "--relative", since],
        cwd=project_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        result = subprocess.run(  # noqa: S603
            [git, "diff", "--name-only", "--relative", f"{since}..HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
    if result.returncode != 0:
        return set()
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _path_matches_changed(path: Path, project_root: Path, changed: set[str]) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    if rel in changed:
        return True
    if path.is_dir():
        prefix = f"{rel}/"
        return any(item.startswith(prefix) for item in changed)
    parent = str(Path(rel).parent)
    if parent == ".":
        return False
    prefix = f"{parent}/"
    return any(item.startswith(prefix) for item in changed)
