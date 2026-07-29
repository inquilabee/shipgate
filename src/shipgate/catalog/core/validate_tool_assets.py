"""Bundled asset and conditional gate validation for catalog tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import ToolDefinition


def validate_tool_bundled_config(
    tool: ToolDefinition,
    *,
    bundled_root: Path | None,
) -> None:
    if tool.configuration.bundled and bundled_root is not None:
        bundled_path = bundled_root / tool.configuration.bundled
        if not bundled_path.is_file():
            raise CatalogError(f"tool {tool.id!r} missing bundled config: {bundled_path}")


def validate_tool_script(
    tool: ToolDefinition,
    *,
    bundled_root: Path | None,
) -> None:
    if tool.script and tool.module:
        raise CatalogError(
            f"tool {tool.id!r} cannot set both script and module",
        )
    if not tool.script or bundled_root is None:
        return
    script_path = bundled_root / tool.script
    if not script_path.is_file():
        raise CatalogError(f"tool {tool.id!r} missing bundled script: {script_path}")


def validate_tool_module(tool: ToolDefinition) -> None:
    if not tool.module:
        return
    if not isinstance(tool.module, str) or not tool.module.strip():
        raise CatalogError(f"tool {tool.id!r} module must be a non-empty string")
    if "/" in tool.module or tool.module.endswith(".py"):
        raise CatalogError(
            f"tool {tool.id!r} module must be an import path (got {tool.module!r})",
        )


def validate_tool_cache(tool: ToolDefinition) -> None:
    if tool.cache is None:
        return
    if tool.cache.ttl_seconds is not None and tool.cache.ttl_seconds < 0:
        raise CatalogError(f"tool {tool.id!r} cache.ttl_seconds must be >= 0")


def validate_suggest_if(tool: ToolDefinition) -> None:
    if tool.suggest_if is None:
        return
    if not tool.suggest_if.files_present:
        raise CatalogError(f"tool {tool.id!r} suggest_if.files_present must not be empty")


def validate_require_if(tool: ToolDefinition) -> None:
    if tool.require_if is None:
        return
    if not tool.require_if.files_present:
        raise CatalogError(f"tool {tool.id!r} require_if.files_present must not be empty")
