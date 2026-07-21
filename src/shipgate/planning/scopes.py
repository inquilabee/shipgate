"""Scope resolution."""

from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig, Scope
from shipgate.planning.gitignore import should_ignore

DEFAULT_EXCLUDES = (".shipgate/", ".venv/", "build/", "reports/", "__pycache__/")


def resolve_scope(
    project_root: Path,
    project: ProjectConfig,
    *,
    target_override: Path | None = None,
    scope_name: str | None = None,
) -> Scope:
    if scope_name and project.scopes and scope_name in project.scopes:
        return project.scopes[scope_name]
    target = (target_override or project.target).resolve()
    if not target.is_absolute():
        target = (project_root / target).resolve()
    exclude = tuple(DEFAULT_EXCLUDES)
    return Scope(target=target, exclude=exclude, respect_gitignore=True)


def scope_paths(scope: Scope, project_root: Path, *, mode: RunMode) -> tuple[Path, ...]:
    if mode == RunMode.APPLY:
        return (scope.target,)
    if not scope.respect_gitignore and not scope.include and not scope.exclude:
        return (scope.target,)
    paths = _scope_entry_paths(project_root, scope)
    return tuple(paths) if paths else (scope.target,)


def _scope_entry_paths(project_root: Path, scope: Scope) -> list[Path]:
    target = scope.target.resolve()
    project_root = project_root.resolve()
    if target.is_file():
        return _scope_file_path(project_root, target, scope)
    if target != project_root:
        return _scope_directory_path(project_root, target, scope)
    return _scope_project_root_dirs(project_root, scope)


def _scope_file_path(project_root: Path, target: Path, scope: Scope) -> list[Path]:
    if should_ignore(project_root, target, extra_excludes=scope.exclude):
        return []
    if scope.include and not _path_matches_include(project_root, target, scope.include):
        return []
    return [target]


def _scope_directory_path(project_root: Path, target: Path, scope: Scope) -> list[Path]:
    if should_ignore(project_root, target, extra_excludes=scope.exclude):
        return []
    if scope.include and not _path_matches_include(project_root, target, scope.include):
        return []
    return [target]


def _scope_project_root_dirs(project_root: Path, scope: Scope) -> list[Path]:
    if scope.include:
        entries: list[Path] = []
        for inc in scope.include:
            path = (project_root / inc).resolve()
            try:
                path.relative_to(project_root.resolve())
            except ValueError:
                continue
            if not path.exists():
                continue
            if should_ignore(project_root, path, extra_excludes=scope.exclude):
                continue
            entries.append(path)
        return sorted(entries)
    entries: list[Path] = []
    for child in sorted(project_root.iterdir()):
        if not child.is_dir():
            continue
        if should_ignore(project_root, child, extra_excludes=scope.exclude):
            continue
        if scope.include and not _path_matches_include(project_root, child, scope.include):
            continue
        entries.append(child)
    return entries


def _path_matches_include(project_root: Path, path: Path, include: tuple[str, ...]) -> bool:
    rel = path.relative_to(project_root).as_posix()
    if path.is_file():
        return any(rel.startswith(inc.rstrip("/")) for inc in include)
    return any(
        rel.startswith(inc.rstrip("/")) or inc.rstrip("/").startswith(rel) for inc in include
    )
