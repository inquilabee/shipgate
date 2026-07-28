"""Suite and check planning."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.errors import PlanningError
from shipgate.planning.core.checks import check_name_tool_pairs
from shipgate.planning.core.suites import expand_suite

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog
    from shipgate.domain.project import ProjectConfig


@dataclass(frozen=True)
class SelectedTool:
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
) -> tuple[str, list[SelectedTool]]:
    """Return (run_label, selected tools) for the given mode and overrides."""
    if check_override:
        return resolve_check_override(check_override, mode, project, catalog)
    if project.checks and not suite_override:
        selected = selected_from_check_names(project, catalog, mode)
        return project.suite or "custom", selected
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
) -> tuple[str, list[SelectedTool]]:
    if not catalog.is_tool(check_override):
        raise PlanningError(
            f"unknown check {check_override!r}",
            hint='run "shipgate list checks" to see bundled checks',
        )
    scope_name = project.scope_for_check(check_override)
    return check_override, [
        SelectedTool(
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
) -> tuple[str, list[SelectedTool]]:
    suite_id = suite_override or (
        "format" if mode == RunMode.APPLY else (project.suite or "standard")
    )

    tool_ids = expand_suite(suite_id, catalog)
    selected = [
        SelectedTool(
            tool_id=tool_id,
            mode=mode,
            scope_name=project.scope_for_check(tool_id),
        )
        for tool_id in tool_ids
    ]
    return suite_id, selected


def selected_from_check_names(
    project: ProjectConfig,
    catalog: Catalog,
    mode: RunMode,
) -> list[SelectedTool]:
    selected: list[SelectedTool] = []
    seen: set[str] = set()
    check_names = project.checks or tuple(binding.runnable for binding in project.check_bindings)
    for check_name, tool_id in check_name_tool_pairs(check_names, catalog):
        if tool_id in seen:
            continue
        seen.add(tool_id)
        selected.append(
            SelectedTool(
                tool_id=tool_id,
                mode=mode,
                scope_name=project.scope_for_check(tool_id) or project.scope_for_check(check_name),
            )
        )
    return selected


def suite_execution_flags(
    catalog: Catalog,
    suite_id: str,
    project: ProjectConfig,
) -> tuple[bool, bool]:
    if catalog.is_suite(suite_id):
        suite = catalog.get_suite(suite_id)
        return suite.parallel, suite.fail_fast
    return project.parallel, project.fail_fast
