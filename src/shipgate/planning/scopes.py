"""Scope resolution."""

from pathlib import Path

from shipgate.domain.project import ProjectConfig, Scope

DEFAULT_EXCLUDES = (".shipgate/", ".venv/", "reports/", "__pycache__/")


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


def scope_paths(scope: Scope) -> tuple[Path, ...]:
    return (scope.target,)
