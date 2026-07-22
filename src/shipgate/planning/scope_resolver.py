"""Scope resolution."""

from __future__ import annotations

from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig, Scope
from shipgate.planning.gitignore import should_ignore

DEFAULT_EXCLUDES = (".shipgate/", ".venv/", "build/", "reports/", "__pycache__/")


class ScopeResolver:
    def __init__(
        self,
        project_root: Path,
        *,
        default_excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    ) -> None:
        self.project_root = project_root.resolve()
        self.default_excludes = default_excludes

    def resolve(
        self,
        project: ProjectConfig,
        *,
        target_override: Path | None = None,
        scope_name: str | None = None,
    ) -> Scope:
        if scope_name and project.scopes and scope_name in project.scopes:
            return project.scopes[scope_name]
        target = (target_override or project.target).resolve()
        if not target.is_absolute():
            target = (self.project_root / target).resolve()
        return Scope(target=target, exclude=self.default_excludes, respect_gitignore=True)

    def paths(self, scope: Scope, *, mode: RunMode) -> tuple[Path, ...]:
        if mode == RunMode.APPLY:
            return (self._relative_if_under_root(scope.target),)
        if not scope.respect_gitignore and not scope.include and not scope.exclude:
            return (scope.target,)
        paths = self._scope_entry_paths(scope)
        return tuple(paths) if paths else (scope.target,)

    def _scope_entry_paths(self, scope: Scope) -> list[Path]:
        target = scope.target.resolve()
        if target.is_file() or target != self.project_root:
            return self._scope_single_path(target, scope)
        return self._scope_project_root_dirs(scope)

    def _scope_single_path(self, target: Path, scope: Scope) -> list[Path]:
        if should_ignore(self.project_root, target, extra_excludes=scope.exclude):
            return []
        if scope.include and not self._path_matches_include(target, scope.include):
            return []
        return [target]

    def _scope_project_root_dirs(self, scope: Scope) -> list[Path]:
        if scope.include:
            return self._scope_included_dirs(scope)
        return self._scope_default_dirs(scope)

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
        if not path.exists():
            return False
        return not should_ignore(self.project_root, path, extra_excludes=scope.exclude)

    def _path_matches_include(self, path: Path, include: tuple[str, ...]) -> bool:
        rel = path.relative_to(self.project_root).as_posix()
        if path.is_file():
            return any(rel.startswith(inc.rstrip("/")) for inc in include)
        return any(
            rel.startswith(inc.rstrip("/")) or inc.rstrip("/").startswith(rel) for inc in include
        )

    def _relative_if_under_root(self, path: Path) -> Path:
        resolved = path.resolve()
        try:
            rel = resolved.relative_to(self.project_root)
        except ValueError:
            return path
        return rel if rel.parts else Path()
