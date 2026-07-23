"""Catalog tool inheritance resolution."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from shipgate.config.merge import deep_merge_config
from shipgate.errors import CatalogError

EXTENDS_KEY = "extends"


class ToolExtendsResolver:
    """Resolve ``extends`` inheritance for bundled and project tool definitions.

    Deep-merges parent tool YAML into children and detects unknown parents and cycles.
    """

    def __init__(
        self,
        bundled_tools: dict[str, dict[str, Any]],
        project_tools: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self._bundled_tools = bundled_tools
        self._project_tools = project_tools or {}
        self._effective_raw = dict(bundled_tools)
        self._effective_raw.update(self._project_tools)
        self._resolved: dict[str, dict[str, Any]] = {}
        self._resolving: set[str] = set()

    @classmethod
    def resolve(
        cls,
        bundled_tools: dict[str, dict[str, Any]],
        project_tools: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        return cls(bundled_tools, project_tools)._resolve_all()

    def _resolve_all(self) -> dict[str, dict[str, Any]]:
        for tool_id in sorted(self._effective_raw):
            self._resolve_tool(tool_id)
        return self._resolved

    def _resolve_tool(self, tool_id: str, *, stack: tuple[str, ...] = ()) -> dict[str, Any]:
        if tool_id in self._resolved:
            return self._resolved[tool_id]
        if tool_id in self._resolving:
            chain = " -> ".join([*stack, tool_id])
            raise CatalogError(f"tool inheritance cycle detected: {chain}")
        if tool_id not in self._effective_raw:
            raise CatalogError(
                f"tool {tool_id!r} extends unknown parent",
                hint='run "shipgate list tools" to see bundled tools',
            )

        raw = self._effective_raw[tool_id]
        extends = raw.get(EXTENDS_KEY)
        if extends is None:
            self._resolved[tool_id] = deepcopy(raw)
            return self._resolved[tool_id]

        if not isinstance(extends, str):
            raise CatalogError(f"tool {tool_id!r} extends must be a tool id string")

        parent_id = extends
        if parent_id == tool_id and tool_id not in self._bundled_tools:
            raise CatalogError(f"tool {tool_id!r} cannot extend itself")

        self._resolving.add(tool_id)
        parent = self._resolve_parent(tool_id, parent_id, stack=(*stack, tool_id))
        overlay = {key: value for key, value in raw.items() if key != EXTENDS_KEY}
        self._resolved[tool_id] = deep_merge_config(parent, overlay)
        self._resolving.remove(tool_id)
        return self._resolved[tool_id]

    def _resolve_parent(
        self,
        tool_id: str,
        parent_id: str,
        *,
        stack: tuple[str, ...],
    ) -> dict[str, Any]:
        if tool_id == parent_id:
            if parent_id not in self._bundled_tools:
                raise CatalogError(f"tool {tool_id!r} cannot extend itself")
            parent_raw = self._bundled_tools[parent_id]
            if EXTENDS_KEY not in parent_raw:
                return deepcopy(parent_raw)
            return self._resolve_tool(parent_id, stack=stack)

        if parent_id in self._resolved:
            return deepcopy(self._resolved[parent_id])

        if parent_id not in self._effective_raw:
            raise CatalogError(
                f"tool {tool_id!r} extends unknown parent {parent_id!r}",
                hint='run "shipgate list tools" to see bundled tools',
            )

        parent_raw = self._effective_raw[parent_id]
        if EXTENDS_KEY in parent_raw:
            return self._resolve_tool(parent_id, stack=stack)
        return deepcopy(parent_raw)
