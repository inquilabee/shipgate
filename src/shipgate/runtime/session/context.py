"""Run session types and context preparation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.ci import apply_ci_defaults, is_ci_environment
from shipgate.config.loader import load_config
from shipgate.planning.incremental import RunScopeSession, effective_incremental
from shipgate.planning.workflow import resolve_runnables, suite_execution_flags
from shipgate.runtime.environment import resolve_environment

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog
    from shipgate.domain.execution import ExecutionEnvironment
    from shipgate.domain.modes import RunMode
    from shipgate.domain.project import ProjectConfig
    from shipgate.planning.workflow import PlannedCheck


@dataclass(frozen=True)
class RunCommand:
    project_root: Path
    config_path: Path | None = None
    suite: str | None = None
    check: str | None = None
    workflow: str | None = None
    target: Path | None = None
    error_format: str | None = None
    extra_args: tuple[str, ...] = ()
    verbose: bool = False
    quiet: bool = False
    display_cli: bool = False
    ci: bool = False
    no_cache: bool = False
    changed_only: bool = False
    since: str | None = None


@dataclass(frozen=True)
class RunProgress:
    current_check_id: str
    checks_completed: int
    checks_total: int


@dataclass(frozen=True)
class RunContext:
    project: ProjectConfig
    project_root: Path
    suite_id: str
    planned_checks: tuple[PlannedCheck, ...]
    environment: ExecutionEnvironment
    parallel: bool
    fail_fast: bool
    scope_session: RunScopeSession


def resolve_error_format(command: RunCommand, project: ProjectConfig) -> str:
    explicit = command.error_format or project.error_format
    if command.ci or is_ci_environment():
        return apply_ci_defaults(explicit)
    return explicit or "json"


def prepare_context(command: RunCommand, mode: RunMode, catalog: Catalog) -> RunContext:
    project = load_config(
        config_path=command.config_path,
        project_root=command.project_root,
    )
    project_root = command.project_root.resolve()
    suite_id, planned_checks = resolve_runnables(
        mode=mode,
        project=project,
        catalog=catalog,
        suite_override=command.suite,
        check_override=command.check,
        workflow_override=command.workflow,
    )
    parallel, fail_fast = suite_execution_flags(catalog, suite_id, project)
    environment = resolve_environment(project_root, project.env)
    changed_only, since = effective_incremental(command, project)
    scope_session = RunScopeSession(
        project_root=project_root,
        changed_only=changed_only,
        since=since,
    )
    return RunContext(
        project=project,
        project_root=project_root,
        suite_id=suite_id,
        planned_checks=tuple(planned_checks),
        environment=environment,
        parallel=parallel,
        fail_fast=fail_fast,
        scope_session=scope_session,
    )
