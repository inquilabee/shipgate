"""Workflow planning."""

from shipgate.domain.catalog import Catalog
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.errors import PlanningError
from shipgate.planning.suites import expand_suite


def resolve_runnables(
    *,
    mode: RunMode,
    project: ProjectConfig,
    catalog: Catalog,
    suite_override: str | None = None,
    check_override: str | None = None,
) -> tuple[str, list[str]]:
    """Return (suite_id, tool_ids) for the given mode and overrides."""
    if check_override:
        if not catalog.is_tool(check_override):
            raise PlanningError(
                f"unknown check {check_override!r}",
                hint='run "shipgate list checks" to see bundled checks',
            )
        return check_override, [check_override]

    if mode == RunMode.APPLY:
        suite_id = suite_override or "format"
    else:
        suite_id = suite_override or project.suite or "standard"

    if project.checks and not suite_override:
        tools: list[str] = []
        for check in project.checks:
            tools.extend(expand_suite(check, catalog))
        return suite_id, tools

    tools = expand_suite(suite_id, catalog)
    return suite_id, tools
