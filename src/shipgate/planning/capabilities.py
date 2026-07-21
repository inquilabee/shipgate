"""Capability helpers."""

from shipgate.domain.catalog import Catalog


def tools_by_capability(catalog: Catalog, capability: str) -> list[str]:
    return sorted(
        tool_id for tool_id, tool in catalog.tools.items() if capability in tool.capabilities
    )
