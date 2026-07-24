"""Suite and check planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.errors import PlanningError
from shipgate.planning.suites import expand_suite

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog
    from shipgate.domain.project import ProjectConfig


@dataclass(frozen=True)
class PlannedCheck:
    tool_id: str
    mode: RunMode
    scope_name: str | None = None


def resolve_runnables(
    *,
    mode: RunMode,
    project: ProjectConfig,
    catalog: Catalog,
    suite_override: str | None = None,
    check_override: str | None = None,
) -> tuple[str, list[PlannedCheck]]:
    """Return (run_label, planned checks) for the given mode and overrides."""
    if check_override:
        return resolve_check_override(check_override, mode, project, catalog)
    if project.checks and not suite_override:
        planned = planned_from_check_names(project, catalog, mode)
        return project.suite or "custom", planned
    return resolve_suite(
        mode=mode,
        project=project,
        catalog=catalog,
        suite_override=suite_override,
    )


def resolve_check_override(
    check_override: str,
    mode: RunMode,
    project: ProjectConfig,
    catalog: Catalog,
) -> tuple[str, list[PlannedCheck]]:
    if not catalog.is_tool(check_override):
        raise PlanningError(
            f"unknown check {check_override!r}",
            hint='run "shipgate list checks" to see bundled checks',
        )
    scope_name = project.scope_for_check(check_override)
    return check_override, [
        PlannedCheck(
            tool_id=check_override,
            mode=mode,
            scope_name=scope_name,
        )
    ]


def resolve_suite(
    *,
    mode: RunMode,
    project: ProjectConfig,
    catalog: Catalog,
    suite_override: str | None,
) -> tuple[str, list[PlannedCheck]]:
    if suite_override:
        suite_id = suite_override
    elif mode == RunMode.APPLY:
        suite_id = "format"
    else:
        suite_id = project.suite or "standard"

    tool_ids = expand_suite(suite_id, catalog)
    planned = [
        PlannedCheck(
            tool_id=tool_id,
            mode=mode,
            scope_name=project.scope_for_check(tool_id),
        )
        for tool_id in tool_ids
    ]
    return suite_id, planned


def planned_from_check_names(
    project: ProjectConfig,
    catalog: Catalog,
    mode: RunMode,
) -> list[PlannedCheck]:
    planned: list[PlannedCheck] = []
    seen: set[str] = set()
    check_names = project.checks or tuple(binding.runnable for binding in project.check_bindings)
    for check_name in check_names:
        for tool_id in expand_suite(check_name, catalog):
            if tool_id in seen:
                continue
            seen.add(tool_id)
            planned.append(
                PlannedCheck(
                    tool_id=tool_id,
                    mode=mode,
                    scope_name=project.scope_for_check(tool_id)
                    or project.scope_for_check(check_name),
                )
            )
    return planned


def suite_execution_flags(
    catalog: Catalog,
    suite_id: str,
    project: ProjectConfig,
) -> tuple[bool, bool]:
    if catalog.is_suite(suite_id):
        suite = catalog.get_suite(suite_id)
        return suite.parallel, suite.fail_fast
    return project.parallel, project.fail_fast
