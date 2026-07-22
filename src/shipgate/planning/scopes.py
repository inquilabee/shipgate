"""Scope resolution."""

from pathlib import Path

from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig, Scope
from shipgate.planning.scope_resolver import DEFAULT_EXCLUDES, ScopeResolver

__all__ = ["DEFAULT_EXCLUDES", "ScopeResolver", "resolve_scope", "scope_paths"]


def resolve_scope(
    project_root: Path,
    project: ProjectConfig,
    *,
    target_override: Path | None = None,
    scope_name: str | None = None,
) -> Scope:
    return ScopeResolver(project_root).resolve(
        project,
        target_override=target_override,
        scope_name=scope_name,
    )


def scope_paths(scope: Scope, project_root: Path, *, mode: RunMode) -> tuple[Path, ...]:
    return ScopeResolver(project_root).paths(scope, mode=mode)
