"""Incremental check helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.planning.gitignore import expand_scope, minimize_covering_dirs

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig, Scope
    from shipgate.runtime.session.context import RunCommand

MAX_INCREMENTAL_EXPLICIT_FILES = 64


def effective_incremental(command: RunCommand, project: ProjectConfig) -> tuple[bool, str | None]:
    changed_only = command.changed_only or project.changed_only
    since = command.since if command.since is not None else project.since
    return changed_only, since


def is_incremental(*, changed_only: bool, since: str | None) -> bool:
    return changed_only or since is not None


def tool_paths_after_incremental(
    paths: tuple[Path, ...],
    *,
    tool: ToolDefinition,
    scope: Scope,
    project_root: Path,
    mode: RunMode,
    since: str | None,
    changed_only: bool,
) -> tuple[Path, ...]:
    if not is_incremental(changed_only=changed_only, since=since):
        return paths

    rel_files = matched_changed_files(
        tool=tool,
        scope=scope,
        project_root=project_root,
        since=since,
    )
    if not rel_files:
        return () if changed_only else paths

    return argv_paths_for_incremental(
        rel_files,
        tool=tool,
        mode=mode,
        project_root=project_root,
        fallback=paths,
    )


def argv_paths_for_incremental(
    rel_files: tuple[Path, ...],
    *,
    tool: ToolDefinition,
    mode: RunMode,
    project_root: Path,
    fallback: tuple[Path, ...],
) -> tuple[Path, ...]:
    criteria = tool.scope
    if criteria.delivery == "files":
        return rel_files
    if criteria.delivery == "dirs":
        absolute_files = tuple(project_root / rel for rel in rel_files)
        return minimize_covering_dirs(absolute_files, project_root)

    accepts_paths = "paths" in tool.cli or (mode == RunMode.APPLY and criteria.delivery == "root")
    if not accepts_paths:
        return fallback

    if len(rel_files) <= MAX_INCREMENTAL_EXPLICIT_FILES:
        return rel_files
    absolute_files = tuple(project_root / rel for rel in rel_files)
    dirs = minimize_covering_dirs(absolute_files, project_root)
    return dirs if dirs else rel_files


def matched_changed_files(
    *,
    tool: ToolDefinition,
    scope: Scope,
    project_root: Path,
    since: str | None,
) -> tuple[Path, ...]:
    criteria = tool.scope
    target = scope.target.resolve()
    if not target.is_absolute():
        target = (project_root / target).resolve()

    matched_files = expand_scope(
        project_root,
        target,
        include=scope.include,
        exclude=scope.exclude,
        extensions=criteria.extensions,
        globs=criteria.globs,
        respect_gitignore=scope.respect_gitignore,
    )
    if not matched_files:
        return ()

    ref = since or "HEAD"
    changed = git_changed_files(project_root, ref)
    if not changed:
        return ()

    filtered_files = tuple(
        path for path in matched_files if file_matches_changed(path, project_root, changed)
    )
    return tuple(relative_under_root(path, project_root) for path in filtered_files)


def relative_under_root(path: Path, project_root: Path) -> Path:
    resolved = path.resolve()
    try:
        rel = resolved.relative_to(project_root.resolve())
    except ValueError:
        return path
    return rel if rel.parts else Path()


def git_executable() -> str:
    git = shutil.which("git")
    if git is None:
        return "git"
    return git


def git_changed_files(project_root: Path, since: str) -> set[str]:
    if not (project_root / ".git").exists():
        return set()
    if since == "HEAD":
        return git_changed_against_head(project_root)
    git = git_executable()
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


def git_changed_against_head(project_root: Path) -> set[str]:
    git = git_executable()
    changed: set[str] = set()
    for args in (
        [git, "diff", "--name-only", "--relative", "--cached", "HEAD"],
        [git, "diff", "--name-only", "--relative", "HEAD"],
    ):
        result = subprocess.run(  # noqa: S603
            args,
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue
        changed |= {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return changed


def file_matches_changed(path: Path, project_root: Path, changed: set[str]) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    return rel in changed
