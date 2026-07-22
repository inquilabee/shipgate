"""Scope resolution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.planning.scope_resolver import DEFAULT_EXCLUDES, ScopeResolver

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.modes import RunMode
    from shipgate.domain.project import ProjectConfig, Scope

__all__ = [
    "DEFAULT_EXCLUDES",
    "ScopeResolver",
    "resolve_scope",
    "scope_paths",
    "scope_paths_for_tool",
]


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


def scope_paths_for_tool(
    scope: Scope,
    tool: ToolDefinition,
    project_root: Path,
    *,
    mode: RunMode,
) -> tuple[Path, ...]:
    return ScopeResolver(project_root).paths_for_tool(scope, tool, mode=mode)
