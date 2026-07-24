"""Catalog validation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.domain.ids import validate_id
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError
from shipgate.registries.normalizers import VALID_NORMALIZERS

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition


class CatalogValidator:
    """Validate a parsed ``Catalog`` against catalog schema and referential rules.

    Checks tool CLI, scope, install metadata, suite membership, and bundled assets.
    """

    VALID_CLI_STYLES = frozenset({"positional", "scalar", "repeated", "joined", "boolean"})
    VALID_CLI_AGGREGATES = frozenset({"repeat", "root"})
    VALID_SCOPE_DELIVERY = frozenset({"root", "dirs", "files"})

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
        self._validate_suite_members()

    def _is_known_suite_member(self, member: str) -> bool:
        return member in self._catalog.tools or member in self._catalog.suites

    def _validate_suite_members(self) -> None:
        for suite_id, suite in self._catalog.suites.items():
            self._validate_tool_id(suite_id)
            if not suite.members:
                raise CatalogError(f"suite {suite_id!r} has no members")
            for member in suite.members:
                if not self._is_known_suite_member(member):
                    raise CatalogError(
                        f"suite {suite_id!r} references unknown member {member!r}",
                        hint='run "shipgate list tools" to see bundled tools',
                    )
        for suite_id in self._catalog.suites:
            self._detect_suite_cycle(suite_id)

    def _validate_tool_id(self, tool_id: str) -> None:
        try:
            validate_id(tool_id, kind="tool id")
        except ValueError as exc:
            raise CatalogError(str(exc)) from exc

    def _validate_tool(self, tool: ToolDefinition) -> None:
        self._validate_tool_cli(tool)
        self._validate_tool_normalizer(tool)
        self._validate_tool_modes(tool)
        self._validate_tool_scope(tool)
        self._validate_tool_bundled_config(tool)
        self._validate_tool_script(tool)
        self._validate_tool_install(tool)

    def _validate_tool_cli(self, tool: ToolDefinition) -> None:
        for name, opt in tool.cli.items():
            if opt.style not in self.VALID_CLI_STYLES:
                raise CatalogError(
                    f"tool {tool.id!r} option {name!r} has unsupported style {opt.style!r}"
                )
            if opt.aggregate is not None and opt.aggregate not in self.VALID_CLI_AGGREGATES:
                raise CatalogError(
                    f"tool {tool.id!r} option {name!r} has unsupported aggregate {opt.aggregate!r}"
                )

    def _validate_tool_normalizer(self, tool: ToolDefinition) -> None:
        if tool.normalizer not in VALID_NORMALIZERS:
            raise CatalogError(f"tool {tool.id!r} has unknown normalizer {tool.normalizer!r}")

    def _validate_tool_modes(self, tool: ToolDefinition) -> None:
        for mode in tool.modes:
            if not isinstance(mode, RunMode):
                raise CatalogError(f"tool {tool.id!r} has invalid mode {mode!r}")

    def _validate_tool_scope(self, tool: ToolDefinition) -> None:
        delivery = tool.scope.delivery
        if delivery not in self.VALID_SCOPE_DELIVERY:
            raise CatalogError(
                f"tool {tool.id!r} has unsupported scope delivery {delivery!r}",
            )
        has_criteria = bool(tool.scope.extensions or tool.scope.globs)
        if delivery == "files" and not has_criteria:
            raise CatalogError(
                f"tool {tool.id!r} with delivery 'files' requires extensions or globs",
            )
        if tool.script is not None and delivery not in {"files", "dirs"}:
            raise CatalogError(
                f"gate tool {tool.id!r} must use delivery 'files' or 'dirs'",
            )

    def _validate_tool_bundled_config(self, tool: ToolDefinition) -> None:
        if tool.configuration.bundled and self._bundled_root is not None:
            bundled_path = self._bundled_root / tool.configuration.bundled
            if not bundled_path.is_file():
                raise CatalogError(f"tool {tool.id!r} missing bundled config: {bundled_path}")

    def _validate_tool_script(self, tool: ToolDefinition) -> None:
        if not tool.script or self._bundled_root is None:
            return
        script_path = self._bundled_root / tool.script
        if not script_path.is_file():
            raise CatalogError(f"tool {tool.id!r} missing bundled script: {script_path}")

    def _validate_tool_install(self, tool: ToolDefinition) -> None:
        if tool.install is not None and tool.install.manager not in ("python", "binary"):
            raise CatalogError(f"tool {tool.id!r} has unsupported install manager")

    def _detect_suite_cycle(self, start: str) -> None:
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> None:
            if node in stack:
                cycle = " -> ".join([*stack, node])
                raise CatalogError(f"suite cycle detected: {cycle}")
            if node in visited:
                return
            if node not in self._catalog.suites:
                return
            stack.append(node)
            for member in self._catalog.suites[node].members:
                if member in self._catalog.suites:
                    visit(member)
            stack.pop()
            visited.add(node)

        visit(start)
