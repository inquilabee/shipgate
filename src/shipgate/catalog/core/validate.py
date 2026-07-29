"""Catalog validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.core.validate_suite import validate_suite_members
from shipgate.catalog.core.validate_tool_assets import (
    validate_require_if,
    validate_suggest_if,
    validate_tool_bundled_config,
    validate_tool_cache,
    validate_tool_module,
    validate_tool_script,
)
from shipgate.catalog.core.validate_tool_cli_scope import (
    validate_tool_cli,
    validate_tool_modes,
    validate_tool_normalizer,
    validate_tool_scope,
)
from shipgate.catalog.core.validate_tool_install import validate_tool_install
from shipgate.domain.ids import validate_id
from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition


class CatalogValidator:
    """Validate a parsed ``Catalog`` against catalog schema and referential rules.

    Checks tool CLI, scope, install metadata, suite membership, and bundled assets.
    """

    def __init__(self, catalog: Catalog, bundled_root: Path | None = None) -> None:
        self._catalog = catalog
        self._bundled_root = bundled_root

    @classmethod
    def validate(cls, catalog: Catalog, bundled_root: Path | None = None) -> None:
        cls(catalog, bundled_root)._validate()

    def _validate(self) -> None:
        for tool_id, tool in self._catalog.tools.items():
            self._validate_tool_id(tool_id)
            self._validate_tool(tool)
        validate_suite_members(self._catalog)

    @staticmethod
    def _validate_tool_id(tool_id: str) -> None:
        try:
            validate_id(tool_id, kind="tool id")
        except ValueError as exc:
            raise CatalogError(str(exc)) from exc

    def _validate_tool(self, tool: ToolDefinition) -> None:
        validate_tool_cli(tool)
        validate_tool_normalizer(tool)
        validate_tool_modes(tool)
        validate_tool_scope(tool)
        validate_tool_bundled_config(tool, bundled_root=self._bundled_root)
        validate_tool_script(tool, bundled_root=self._bundled_root)
        validate_tool_module(tool)
        validate_tool_install(tool)
        validate_tool_cache(tool)
        validate_suggest_if(tool)
        validate_require_if(tool)
