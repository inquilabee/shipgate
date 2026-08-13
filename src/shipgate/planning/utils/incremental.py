"""Incremental check helpers."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.domain.modes import RunMode
from shipgate.errors import PlanningError
from shipgate.paths import relative_if_under
from shipgate.planning.core.scope_resolver import ExpandScopeKey, ScopeResolver
from shipgate.planning.utils.gitignore import expand_scope, minimize_covering_dirs

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig, Scope
    from shipgate.domain.run_command import RunCommand

MAX_INCREMENTAL_EXPLICIT_FILES = 64
GIT_NAME_ONLY = "--name-only"
GIT_RELATIVE = "--relative"


@dataclass
class RunScopeSession:
    """Caches git change sets and incremental clean state for one run session."""

    project_root: Path
    changed_only: bool
    since: str | None
    _git_changed_cache: dict[str, set[str]] = field(default_factory=dict)
    expand_cache: dict[ExpandScopeKey, tuple[Path, ...]] = field(default_factory=dict)
    _incremental_clean: bool | None = None

    def _compute_incremental_clean(self) -> bool:
        return (
            False
            if not self.changed_only
            or not is_incremental(changed_only=self.changed_only, since=self.since)
            else not self.changed_files(self.since)
        )

    def is_incremental_clean(self) -> bool:
        self._incremental_clean = (
            self._compute_incremental_clean()
            if self._incremental_clean is None
            else self._incremental_clean
        )
        return self._incremental_clean

    def changed_files(self, since: str | None) -> set[str]:
        ref = since or "HEAD"
        if ref not in self._git_changed_cache:
            self._git_changed_cache[ref] = git_changed_files(self.project_root, ref)
        return self._git_changed_cache[ref]


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
    scope_session: RunScopeSession | None = None,
) -> tuple[Path, ...]:
    if scope_session is not None and scope_session.is_incremental_clean():
        return ()

    if not is_incremental(changed_only=changed_only, since=since):
        return paths

    rel_files = matched_changed_files(
        tool=tool,
        scope=scope,
        project_root=project_root,
        since=since,
        scope_session=scope_session,
    )
    return (
        argv_paths_for_incremental(
            rel_files,
            tool=tool,
            mode=mode,
            project_root=project_root,
            fallback=paths,
        )
        if rel_files
        else (() if changed_only else paths)
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
    return argv_paths_for_root_delivery(
        rel_files,
        tool=tool,
        mode=mode,
        project_root=project_root,
        fallback=fallback,
    )


def argv_paths_for_root_delivery(
    rel_files: tuple[Path, ...],
    *,
    tool: ToolDefinition,
    mode: RunMode,
    project_root: Path,
    fallback: tuple[Path, ...],
) -> tuple[Path, ...]:
    paths_opt = tool.cli.get("paths")
    if paths_opt is not None and paths_opt.aggregate == "root":
        # Tools like deptry/gitleaks need a directory ROOT, not file paths.
        return fallback

    accepts_paths = "paths" in tool.cli or (mode == RunMode.APPLY and tool.scope.delivery == "root")
    if not accepts_paths:
        return fallback

    if len(rel_files) <= MAX_INCREMENTAL_EXPLICIT_FILES:
        return rel_files
    absolute_files = tuple(project_root / rel for rel in rel_files)
    dirs = minimize_covering_dirs(absolute_files, project_root)
    return dirs or rel_files


def matched_changed_files(
    *,
    tool: ToolDefinition,
    scope: Scope,
    project_root: Path,
    since: str | None,
    scope_session: RunScopeSession | None = None,
) -> tuple[Path, ...]:
    criteria = tool.scope
    target = scope.target.resolve()
    target = target if target.is_absolute() else (project_root / target).resolve()

    matched_files = (
        ScopeResolver(project_root, scope_session=scope_session)._expand_scope(
            target,
            include=scope.include,
            exclude=scope.exclude,
            extensions=criteria.extensions,
            globs=criteria.globs,
            respect_gitignore=scope.respect_gitignore,
        )
        if scope_session is not None
        else expand_scope(
            project_root,
            target,
            include=scope.include,
            exclude=scope.exclude,
            extensions=criteria.extensions,
            globs=criteria.globs,
            respect_gitignore=scope.respect_gitignore,
        )
    )
    if not matched_files:
        return ()

    ref = since or "HEAD"
    changed = (
        scope_session.changed_files(since)
        if scope_session is not None
        else git_changed_files(project_root, ref)
    )
    if not changed:
        return ()

    filtered_files = tuple(
        path for path in matched_files if file_matches_changed(path, project_root, changed)
    )
    return relatives_under_root(filtered_files, project_root)


def relatives_under_root(paths: tuple[Path, ...], project_root: Path) -> tuple[Path, ...]:
    return tuple(
        rel for path in paths if (rel := relative_under_root(path, project_root)) is not None
    )


def relative_under_root(path: Path, project_root: Path) -> Path | None:
    return relative_if_under(path, project_root)


def git_executable() -> str:
    git = shutil.which("git")
    return "git" if git is None else git


def require_git_ref(since: str) -> str:
    if not since or since.startswith("-"):
        raise PlanningError(
            f"invalid or unresolvable --since ref {since!r}",
            hint="refs must not start with '-'",
        )
    return since


def git_changed_files(project_root: Path, since: str) -> set[str]:
    ref = require_git_ref(since)
    if not (project_root / ".git").exists():
        raise PlanningError(
            "changed-only/--since requires a git repository",
            path=str(project_root),
            hint="run from a git checkout or disable changed-only",
        )
    if ref == "HEAD":
        return git_changed_against_head(project_root)
    git = git_executable()
    result = run_command(
        [git, "diff", GIT_NAME_ONLY, GIT_RELATIVE, ref, "--"],
        cwd=project_root,
    )
    if result.returncode != 0:
        result = run_command(
            [git, "diff", GIT_NAME_ONLY, GIT_RELATIVE, f"{ref}..HEAD", "--"],
            cwd=project_root,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or "").strip()
            raise PlanningError(
                f"invalid or unresolvable --since ref {since!r}",
                hint=detail or 'check the ref with "git rev-parse"',
            )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def git_changed_against_head(project_root: Path) -> set[str]:
    git = git_executable()
    changed: set[str] = set()
    commands = (
        [git, "diff", GIT_NAME_ONLY, GIT_RELATIVE, "--cached", "HEAD"],
        [git, "diff", GIT_NAME_ONLY, GIT_RELATIVE, "HEAD"],
        [git, "ls-files", "--others", "--exclude-standard"],
    )
    failures = 0
    for args in commands:
        result = run_command(args, cwd=project_root)
        if result.returncode != 0:
            failures += 1
            continue
        changed |= {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if failures == len(commands):
        raise PlanningError(
            "git failed while computing changed files",
            path=str(project_root),
        )
    return changed


def file_matches_changed(path: Path, project_root: Path, changed: set[str]) -> bool:
    try:
        rel = path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        rel = path.as_posix()
    return rel in changed
