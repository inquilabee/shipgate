"""Scope resolution."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.domain.project import Scope
from shipgate.planning.utils.gitignore import (
    expand_scope,
    minimize_covering_dirs,
    should_ignore,
)

if TYPE_CHECKING:
    from shipgate.domain.catalog import ScopeCriteria, ToolDefinition
    from shipgate.domain.project import ProjectConfig
    from shipgate.planning.utils.incremental import RunScopeSession


@dataclass(frozen=True)
class ExpandScopeKey:
    target: str
    include: tuple[str, ...]
    exclude: tuple[str, ...]
    extensions: tuple[str, ...]
    globs: tuple[str, ...]
    respect_gitignore: bool


DEFAULT_EXCLUDES = (
    ".shipgate/",
    ".venv/",
    "venv/",
    "build/",
    "reports/",
    "__pycache__/",
)


class ScopeResolver:
    def __init__(
        self,
        project_root: Path,
        *,
        default_excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
        scope_session: RunScopeSession | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        self.default_excludes = default_excludes
        self._scope_session = scope_session

    def resolve(
        self,
        project: ProjectConfig,
        *,
        target_override: Path | None = None,
        scope_name: str | None = None,
    ) -> Scope:
        if scope_name and project.scopes and scope_name in project.scopes:
            return project.scopes[scope_name]
        raw = target_override or project.target
        target = self._resolve_against_project_root(raw)
        return Scope(target=target, exclude=self.default_excludes, respect_gitignore=True)

    def _resolve_against_project_root(self, path: Path) -> Path:
        """Resolve relative paths against project_root, not process CWD."""
        return path.resolve() if path.is_absolute() else (self.project_root / path).resolve()

    def paths(self, scope: Scope, *, mode: RunMode) -> tuple[Path, ...]:
        if mode == RunMode.APPLY:
            return (self._relative_if_under_root(self.resolve_scope_target(scope)),)
        if not scope.respect_gitignore and not scope.include and not scope.exclude:
            return (self.resolve_scope_target(scope),)
        paths = self._scope_entry_paths(scope)
        return tuple(paths) if paths else (self.resolve_scope_target(scope),)

    def _scope_entry_paths(self, scope: Scope) -> list[Path]:
        target = self.resolve_scope_target(scope)
        return (
            self._scope_single_path(target, scope)
            if target.is_file() or target != self.project_root
            else self._scope_project_root_dirs(scope)
        )

    def _scope_single_path(self, target: Path, scope: Scope) -> list[Path]:
        return (
            []
            if should_ignore(self.project_root, target, extra_excludes=scope.exclude)
            else (
                []
                if scope.include and not self._path_matches_include(target, scope.include)
                else [target]
            )
        )

    def _scope_project_root_dirs(self, scope: Scope) -> list[Path]:
        return (
            self._scope_included_dirs(scope) if scope.include else self._scope_default_dirs(scope)
        )

    def _scope_included_dirs(self, scope: Scope) -> list[Path]:
        entries: list[Path] = []
        for inc in scope.include:
            path = (self.project_root / inc).resolve()
            if not self._include_path_allowed(path, scope):
                continue
            entries.append(path)
        return sorted(entries)

    def _scope_default_dirs(self, scope: Scope) -> list[Path]:
        entries: list[Path] = []
        for child in sorted(self.project_root.iterdir()):
            if not child.is_dir():
                continue
            if should_ignore(self.project_root, child, extra_excludes=scope.exclude):
                continue
            if scope.include and not self._path_matches_include(child, scope.include):
                continue
            entries.append(child)
        return entries

    def _include_path_allowed(self, path: Path, scope: Scope) -> bool:
        try:
            path.relative_to(self.project_root)
        except ValueError:
            return False
        return (
            not should_ignore(self.project_root, path, extra_excludes=scope.exclude)
            if path.exists()
            else False
        )

    def _path_matches_include(self, path: Path, include: tuple[str, ...]) -> bool:
        rel = path.relative_to(self.project_root).as_posix()
        return (
            any(rel.startswith(inc.rstrip("/")) for inc in include)
            if path.is_file()
            else any(
                rel.startswith(inc.rstrip("/")) or inc.rstrip("/").startswith(rel)
                for inc in include
            )
        )

    def _relative_if_under_root(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(self.project_root)
        except ValueError:
            return path
        return rel if rel.parts else Path()

    def paths_for_tool(
        self,
        scope: Scope,
        tool: ToolDefinition,
        mode: RunMode,
    ) -> tuple[Path, ...]:
        criteria = tool.scope
        if mode == RunMode.APPLY and criteria.delivery == "root":
            return (
                self._paths_for_root_delivery(scope, self.resolve_scope_target(scope))
                if scope.include
                else (Path(),)
            )

        target = self.resolve_scope_target(scope)
        if criteria.delivery == "root":
            return self._paths_for_root_delivery(scope, target)

        if not scope.respect_gitignore and not scope.include and not scope.exclude:
            return self.delivery_paths_without_filter(scope, criteria)

        matched_files = self._expand_scope(
            target,
            include=scope.include,
            exclude=scope.exclude,
            extensions=criteria.extensions,
            globs=criteria.globs,
            respect_gitignore=scope.respect_gitignore,
        )
        return self.paths_for_delivery(
            criteria,
            matched_files,
            target=target,
        )

    def _paths_for_root_delivery(self, scope: Scope, target: Path) -> tuple[Path, ...]:
        if scope.include:
            entries = self._scope_included_dirs(scope)
            return tuple(self.relative_under_root(path) for path in entries)
        return (self.relative_under_root(target),)

    def resolve_scope_target(self, scope: Scope) -> Path:
        return self._resolve_against_project_root(scope.target)

    def relative_under_root(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(self.project_root)
        except ValueError:
            return path
        return rel if rel.parts else Path()

    def delivery_paths_without_filter(
        self,
        scope: Scope,
        criteria: ScopeCriteria,
    ) -> tuple[Path, ...]:
        target = self.relative_under_root(self.resolve_scope_target(scope))
        if criteria.delivery == "root":
            return (target,)
        if criteria.delivery == "dirs":
            resolved = self.resolve_scope_target(scope)
            if resolved.is_dir():
                return (target,)
            parent = target.parent
            return (parent if parent.parts else Path(),)
        return (target,)

    def _expand_scope(
        self,
        target: Path,
        *,
        include: tuple[str, ...],
        exclude: tuple[str, ...],
        extensions: tuple[str, ...],
        globs: tuple[str, ...],
        respect_gitignore: bool,
    ) -> tuple[Path, ...]:
        if self._scope_session is None:
            return expand_scope(
                self.project_root,
                target,
                include=include,
                exclude=exclude,
                extensions=extensions,
                globs=globs,
                respect_gitignore=respect_gitignore,
            )
        key = ExpandScopeKey(
            target=str(target.resolve()),
            include=include,
            exclude=exclude,
            extensions=extensions,
            globs=globs,
            respect_gitignore=respect_gitignore,
        )
        cache = self._scope_session.expand_cache
        if key not in cache:
            cache[key] = expand_scope(
                self.project_root,
                target,
                include=include,
                exclude=exclude,
                extensions=extensions,
                globs=globs,
                respect_gitignore=respect_gitignore,
            )
        return cache[key]

    def paths_for_delivery(
        self,
        criteria: ScopeCriteria,
        matched_files: tuple[Path, ...],
        *,
        target: Path,
    ) -> tuple[Path, ...]:
        return (
            (self.relative_under_root(target),)
            if criteria.delivery == "root"
            else (
                (
                    tuple(self.relative_under_root(path) for path in matched_files)
                    if criteria.delivery == "files"
                    else minimize_covering_dirs(matched_files, self.project_root)
                )
                if matched_files
                else ()
            )
        )
