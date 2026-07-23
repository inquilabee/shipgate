"""Catalog tool inheritance resolution."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from shipgate.config.merge import deep_merge_config
from shipgate.errors import CatalogError

EXTENDS_KEY = "extends"


class ToolExtendsResolver:
    @staticmethod
    def resolve(
        bundled_tools: dict[str, dict[str, Any]],
        project_tools: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, dict[str, Any]]:
        overlay_tools = project_tools or {}
        effective_raw = ToolExtendsResolver._effective_raw(bundled_tools, overlay_tools)
        resolved: dict[str, dict[str, Any]] = {}
        resolving: set[str] = set()

        def resolve_tool(tool_id: str, *, stack: tuple[str, ...] = ()) -> dict[str, Any]:
            if tool_id in resolved:
                return resolved[tool_id]
            if tool_id in resolving:
                chain = " -> ".join([*stack, tool_id])
                raise CatalogError(f"tool inheritance cycle detected: {chain}")
            if tool_id not in effective_raw:
                raise CatalogError(
                    f"tool {tool_id!r} extends unknown parent",
                    hint='run "shipgate list tools" to see bundled tools',
                )

            raw = effective_raw[tool_id]
            extends = raw.get(EXTENDS_KEY)
            if extends is None:
                resolved[tool_id] = deepcopy(raw)
                return resolved[tool_id]

            if not isinstance(extends, str):
                raise CatalogError(f"tool {tool_id!r} extends must be a tool id string")

            parent_id = extends
            if parent_id == tool_id and tool_id not in bundled_tools:
                raise CatalogError(f"tool {tool_id!r} cannot extend itself")

            resolving.add(tool_id)
            parent = ToolExtendsResolver._resolve_parent(
                tool_id,
                parent_id,
                bundled_tools=bundled_tools,
                effective_raw=effective_raw,
                resolved=resolved,
                resolving=resolving,
                stack=(*stack, tool_id),
                resolve_tool=resolve_tool,
            )
            overlay = {key: value for key, value in raw.items() if key != EXTENDS_KEY}
            resolved[tool_id] = deep_merge_config(parent, overlay)
            resolving.remove(tool_id)
            return resolved[tool_id]

        for tool_id in sorted(effective_raw):
            resolve_tool(tool_id)
        return resolved

    @staticmethod
    def _effective_raw(
        bundled_tools: dict[str, dict[str, Any]],
        overlay_tools: dict[str, dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        effective = dict(bundled_tools)
        effective.update(overlay_tools)
        return effective

    @staticmethod
    def _resolve_parent(
        tool_id: str,
        parent_id: str,
        *,
        bundled_tools: dict[str, dict[str, Any]],
        effective_raw: dict[str, dict[str, Any]],
        resolved: dict[str, dict[str, Any]],
        resolving: set[str],
        stack: tuple[str, ...],
        resolve_tool: Any,
    ) -> dict[str, Any]:
        if tool_id == parent_id:
            if parent_id not in bundled_tools:
                raise CatalogError(f"tool {tool_id!r} cannot extend itself")
            parent_raw = bundled_tools[parent_id]
            if EXTENDS_KEY not in parent_raw:
                return deepcopy(parent_raw)
            return resolve_tool(parent_id, stack=stack)

        if parent_id in resolved:
            return deepcopy(resolved[parent_id])

        if parent_id not in effective_raw:
            raise CatalogError(
                f"tool {tool_id!r} extends unknown parent {parent_id!r}",
                hint='run "shipgate list tools" to see bundled tools',
            )

        parent_raw = effective_raw[parent_id]
        if EXTENDS_KEY in parent_raw:
            return resolve_tool(parent_id, stack=stack)
        return deepcopy(parent_raw)


def resolve_tool_extends(
    bundled_tools: dict[str, dict[str, Any]],
    project_tools: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    return ToolExtendsResolver.resolve(bundled_tools, project_tools)
