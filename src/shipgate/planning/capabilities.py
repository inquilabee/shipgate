"""Capability helpers."""

from shipgate.domain.catalog import Catalog
from shipgate.errors import PlanningError


def tools_by_capability(catalog: Catalog, capability: str) -> list[str]:
    if capability in catalog.capabilities:
        return sorted(catalog.capabilities[capability])
    return sorted(
        tool_id for tool_id, tool in catalog.tools.items() if capability in tool.capabilities
    )


def expand_capability(catalog: Catalog, capability: str) -> list[str]:
    tools = tools_by_capability(catalog, capability)
    if not tools:
        raise PlanningError(
            f"unknown capability {capability!r}",
            hint='run "shipgate list tools" to see bundled tools',
        )
    return tools
