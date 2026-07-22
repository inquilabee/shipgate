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
VALID_CLI_AGGREGATES = frozenset({"repeat", "root"})
VALID_SCOPE_DELIVERY = frozenset({"root", "dirs", "files"})
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
        "radon",
        "vulture",
        "deadcode",
        "gate_json",
    }
)


def validate_catalog(catalog: Catalog, bundled_root: Path | None = None) -> None:
    for tool_id, tool in catalog.tools.items():
        validate_tool_id(tool_id)
        validate_tool(tool, bundled_root)
    validate_suite_members(catalog)
    validate_workflows(catalog)
    validate_capabilities(catalog)


def validate_suite_members(catalog: Catalog) -> None:
    for suite_id, suite in catalog.suites.items():
        validate_tool_id(suite_id)
        if not suite.members:
            raise CatalogError(f"suite {suite_id!r} has no members")
        for member in suite.members:
            if member not in catalog.tools and member not in catalog.suites:
                raise CatalogError(
                    f"suite {suite_id!r} references unknown member {member!r}",
                    hint='run "shipgate list tools" to see bundled tools',
                )
    for suite_id in catalog.suites:
        detect_cycle(catalog, suite_id)


def validate_workflows(catalog: Catalog) -> None:
    for workflow_id, workflow in catalog.workflows.items():
        validate_tool_id(workflow_id)
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


def validate_capabilities(catalog: Catalog) -> None:
    for capability, members in catalog.capabilities.items():
        for member in members:
            if member not in catalog.tools:
                raise CatalogError(
                    f"capability {capability!r} references unknown tool {member!r}",
                )


def validate_tool_id(tool_id: str) -> None:
    try:
        validate_id(tool_id, kind="tool id")
    except ValueError as exc:
        raise CatalogError(str(exc)) from exc


def validate_tool(tool: ToolDefinition, bundled_root: Path | None) -> None:
    validate_tool_cli(tool)
    validate_tool_normalizer(tool)
    validate_tool_modes(tool)
    validate_tool_scope(tool)
    validate_tool_bundled_config(tool, bundled_root)
    validate_tool_script(tool, bundled_root)
    validate_tool_install(tool)


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
    has_criteria = bool(tool.scope.extensions or tool.scope.globs)
    if delivery == "files" and not has_criteria:
        raise CatalogError(
            f"tool {tool.id!r} with delivery 'files' requires extensions or globs",
        )
    if "Policy" in tool.capabilities and delivery not in {"files", "dirs"}:
        raise CatalogError(
            f"gate tool {tool.id!r} must use delivery 'files' or 'dirs'",
        )


def validate_tool_bundled_config(tool: ToolDefinition, bundled_root: Path | None) -> None:
    if tool.configuration.bundled and bundled_root is not None:
        bundled_path = bundled_root / tool.configuration.bundled
        if not bundled_path.is_file():
            raise CatalogError(f"tool {tool.id!r} missing bundled config: {bundled_path}")


def validate_tool_script(tool: ToolDefinition, bundled_root: Path | None) -> None:
    if not tool.script or bundled_root is None:
        return
    script_path = bundled_root / tool.script
    if not script_path.is_file():
        raise CatalogError(f"tool {tool.id!r} missing bundled script: {script_path}")


def validate_tool_install(tool: ToolDefinition) -> None:
    if tool.install is not None and tool.install.manager not in ("python", "binary"):
        raise CatalogError(f"tool {tool.id!r} has unsupported install manager")


def detect_cycle(catalog: Catalog, start: str) -> None:
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
