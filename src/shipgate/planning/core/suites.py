"""Suite expansion."""

from shipgate.domain.catalog import Catalog
from shipgate.errors import CatalogError, PlanningError


def expand_suite(runnable_id: str, catalog: Catalog) -> list[str]:
    """Expand a suite or tool ID into a flat list of tool IDs."""
    if catalog.is_tool(runnable_id):
        return [runnable_id]
    if not catalog.is_suite(runnable_id):
        raise PlanningError(
            f"unknown runnable {runnable_id!r}",
            hint='run "shipgate list suites" to see bundled suites',
        )
    return expand_suite_impl(runnable_id, catalog, stack=[])


def expand_suite_impl(suite_id: str, catalog: Catalog, stack: list[str]) -> list[str]:
    if suite_id in stack:
        cycle = " -> ".join([*stack, suite_id])
        raise CatalogError(f"suite cycle detected: {cycle}")
    suite = catalog.get_suite(suite_id)
    result: list[str] = []
    seen: set[str] = set()
    for member in suite.members:
        if catalog.is_tool(member):
            if member not in seen:
                result.append(member)
                seen.add(member)
            continue
        if not catalog.is_suite(member):
            raise PlanningError(f"suite {suite_id!r} references unknown member {member!r}")
        for tool_id in expand_suite_impl(member, catalog, [*stack, suite_id]):
            if tool_id not in seen:
                result.append(tool_id)
                seen.add(tool_id)
    return result
