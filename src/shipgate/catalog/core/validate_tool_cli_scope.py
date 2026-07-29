"""CLI and scope validation for catalog tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError
from shipgate.registries.normalizers import VALID_NORMALIZERS

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition

VALID_CLI_STYLES = frozenset({"positional", "scalar", "repeated", "joined", "boolean"})
VALID_CLI_AGGREGATES = frozenset({"repeat", "root"})
VALID_SCOPE_DELIVERY = frozenset({"root", "dirs", "files"})


def validate_tool_cli(tool: ToolDefinition) -> None:
    for name, opt in tool.cli.items():
        if opt.style not in VALID_CLI_STYLES:
            raise CatalogError(
                f"tool {tool.id!r} option {name!r} has unsupported style {opt.style!r}"
            )
        if opt.aggregate is not None and opt.aggregate not in VALID_CLI_AGGREGATES:
            raise CatalogError(
                f"tool {tool.id!r} option {name!r} has unsupported aggregate {opt.aggregate!r}"
            )


def validate_tool_normalizer(tool: ToolDefinition) -> None:
    if tool.normalizer not in VALID_NORMALIZERS:
        raise CatalogError(f"tool {tool.id!r} has unknown normalizer {tool.normalizer!r}")


def validate_tool_modes(tool: ToolDefinition) -> None:
    for mode in tool.modes:
        if not isinstance(mode, RunMode):
            raise CatalogError(f"tool {tool.id!r} has invalid mode {mode!r}")


def validate_tool_scope(tool: ToolDefinition) -> None:
    delivery = tool.scope.delivery
    if delivery not in VALID_SCOPE_DELIVERY:
        raise CatalogError(
            f"tool {tool.id!r} has unsupported scope delivery {delivery!r}",
        )
    has_criteria = tool.scope.extensions or tool.scope.globs
    if delivery == "files" and not has_criteria:
        raise CatalogError(
            f"tool {tool.id!r} with delivery 'files' requires extensions or globs",
        )
    if (tool.script is not None or tool.module is not None) and delivery not in {
        "files",
        "dirs",
    }:
        raise CatalogError(
            f"gate tool {tool.id!r} must use delivery 'files' or 'dirs'",
        )
