"""Catalog validation."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.domain.ids import validate_id
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog, ToolDefinition

VALID_CLI_STYLES = frozenset({"positional", "scalar", "repeated", "joined", "boolean"})
VALID_NORMALIZERS = frozenset(
    {
        "ruff",
        "generic_exit",
        "bandit",
        "semgrep",
        "codespell",
        "gitleaks",
        "markdownlint",
        "ty",
        "pytest",
        "radon",
        "vulture",
        "deadcode",
    }
)


def validate_catalog(catalog: Catalog, bundled_root: Path | None = None) -> None:
    for tool_id, tool in catalog.tools.items():
        _validate_tool_id(tool_id)
        _validate_tool(tool, bundled_root)
    for suite_id, suite in catalog.suites.items():
        _validate_tool_id(suite_id)
        if not suite.members:
            raise CatalogError(f"suite {suite_id!r} has no members")
    for suite_id, suite in catalog.suites.items():
        for member in suite.members:
            if member not in catalog.tools and member not in catalog.suites:
                raise CatalogError(
                    f"suite {suite_id!r} references unknown member {member!r}",
                    hint='run "shipgate list tools" to see bundled tools',
                )
    for suite_id in catalog.suites:
        _detect_cycle(catalog, suite_id)
    for workflow_id, workflow in catalog.workflows.items():
        _validate_tool_id(workflow_id)
        if not workflow.steps:
            raise CatalogError(f"workflow {workflow_id!r} has no steps")
        for step in workflow.steps:
            for member in step.members:
                if (
                    member not in catalog.tools
                    and member not in catalog.suites
                    and member not in catalog.capabilities
                ):
                    raise CatalogError(
                        f"workflow {workflow_id!r} references unknown member {member!r}",
                    )
    for capability, members in catalog.capabilities.items():
        for member in members:
            if member not in catalog.tools:
                raise CatalogError(
                    f"capability {capability!r} references unknown tool {member!r}",
                )


def _validate_tool_id(tool_id: str) -> None:
    try:
        validate_id(tool_id, kind="tool id")
    except ValueError as exc:
        raise CatalogError(str(exc)) from exc


def _validate_tool(tool: ToolDefinition, bundled_root: Path | None) -> None:
    _validate_tool_cli(tool)
    _validate_tool_normalizer(tool)
    _validate_tool_modes(tool)
    _validate_tool_bundled_config(tool, bundled_root)
    _validate_tool_install(tool)


def _validate_tool_cli(tool: ToolDefinition) -> None:
    for name, opt in tool.cli.items():
        if opt.style not in VALID_CLI_STYLES:
            raise CatalogError(
                f"tool {tool.id!r} option {name!r} has unsupported style {opt.style!r}"
            )


def _validate_tool_normalizer(tool: ToolDefinition) -> None:
    if tool.normalizer not in VALID_NORMALIZERS:
        raise CatalogError(f"tool {tool.id!r} has unknown normalizer {tool.normalizer!r}")


def _validate_tool_modes(tool: ToolDefinition) -> None:
    for mode in tool.modes:
        if not isinstance(mode, RunMode):
            raise CatalogError(f"tool {tool.id!r} has invalid mode {mode!r}")


def _validate_tool_bundled_config(tool: ToolDefinition, bundled_root: Path | None) -> None:
    if tool.configuration.bundled and bundled_root is not None:
        bundled_path = bundled_root / tool.configuration.bundled
        if not bundled_path.is_file():
            raise CatalogError(f"tool {tool.id!r} missing bundled config: {bundled_path}")


def _validate_tool_install(tool: ToolDefinition) -> None:
    if tool.install is not None and tool.install.manager not in ("python", "binary"):
        raise CatalogError(f"tool {tool.id!r} has unsupported install manager")


def _detect_cycle(catalog: Catalog, start: str) -> None:
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> None:
        if node in stack:
            cycle = " -> ".join([*stack, node])
            raise CatalogError(f"suite cycle detected: {cycle}")
        if node in visited:
            return
        if node not in catalog.suites:
            return
        stack.append(node)
        for member in catalog.suites[node].members:
            if member in catalog.suites:
                visit(member)
        stack.pop()
        visited.add(node)

    visit(start)


def bundled_root_path() -> Path:
    return Path(str(resources.files("shipgate.catalog.bundled")))
