"""Gitignore-aware path filtering."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pathspec

DEFAULT_IGNORED = (
    ".shipgate/",
    ".venv/",
    "reports/",
    "__pycache__/",
    ".git/",
)


def default_ignores() -> tuple[str, ...]:
    return DEFAULT_IGNORED


def load_gitignore_spec(project_root: Path) -> pathspec.PathSpec | None:
    patterns: list[str] = []
    gitignore = project_root / ".gitignore"
    if gitignore.is_file():
        for line in gitignore.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                patterns.append(stripped)
    if not patterns:
        return None
    return pathspec.PathSpec.from_lines("gitignore", patterns)


def is_ignored_by_git(project_root: Path, path: Path) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    result = subprocess.run(
        ["git", "check-ignore", "-q", rel_str],
        cwd=project_root,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


def should_ignore(
    project_root: Path,
    path: Path,
    *,
    extra_excludes: tuple[str, ...] = (),
    spec: pathspec.PathSpec | None = None,
) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve())
    except ValueError:
        return True
    rel_str = str(rel).replace("\\", "/")
    for pattern in (*default_ignores(), *extra_excludes):
        pat = pattern.rstrip("/")
        if rel_str == pat or rel_str.startswith(f"{pat}/"):
            return True
    if spec is not None and spec.match_file(rel_str):
        return True
    git_dir = project_root / ".git"
    if git_dir.is_dir():
        return is_ignored_by_git(project_root, path)
    return False


def expand_scope(
    project_root: Path,
    target: Path,
    *,
    include: tuple[str, ...] = (),
    exclude: tuple[str, ...] = (),
) -> tuple[Path, ...]:
    """Expand a scope target into concrete file paths."""
    project_root = project_root.resolve()
    target = target.resolve() if target.is_absolute() else (project_root / target).resolve()
    spec = load_gitignore_spec(project_root)
    paths: list[Path] = []

    def walk(directory: Path) -> None:
        if not directory.is_dir():
            return
        for child in sorted(directory.iterdir()):
            if should_ignore(project_root, child, extra_excludes=exclude, spec=spec):
                continue
            if child.is_file():
                if include:
                    rel = str(child.relative_to(project_root)).replace("\\", "/")
                    if not any(rel.startswith(inc.rstrip("/")) for inc in include):
                        continue
                paths.append(child)
            elif child.is_dir():
                walk(child)

    if target.is_file():
        if not should_ignore(project_root, target, extra_excludes=exclude, spec=spec):
            paths.append(target)
    else:
        walk(target)
    return tuple(paths)
