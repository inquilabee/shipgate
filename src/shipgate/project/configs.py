"""Project config listing and diff helpers."""

from __future__ import annotations

import difflib
from typing import TYPE_CHECKING

from shipgate.adapter.config_resolve import resolve_config_paths
from shipgate.planning.core.suites import expand_suite
from shipgate.project.config_setup import bundled_template_path, project_config_relpath

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, ToolDefinition
    from shipgate.domain.project import ProjectConfig


def sync_configs(project_root: Path, _catalog: Catalog) -> list[Path]:
    from shipgate.project.init import scaffold_project_layout

    return scaffold_project_layout(project_root)


def display_config_path(project_root: Path, path: Path) -> Path:
    if path.is_relative_to(project_root):
        return path.relative_to(project_root)
    return path


def list_resolved_configs(
    project_root: Path,
    catalog: Catalog,
    project: ProjectConfig,
    *,
    suite: str | None = None,
) -> list[str]:
    suite_id = suite or project.suite or "standard"
    tool_ids = expand_suite(suite_id, catalog)
    lines: list[str] = []
    for tool_id in sorted(tool_ids):
        tool = catalog.get_tool(tool_id)
        if not tool.configuration.bundled and not tool.configuration.discover:
            continue
        paths = resolve_config_paths(tool, project, project_root)
        if paths:
            rel = display_config_path(project_root, paths[0])
            lines.append(f"{tool_id}: {rel}")
        else:
            lines.append(f"{tool_id}: (none)")
    return lines


def diff_tool_config(project_root: Path, tool: ToolDefinition) -> str | None:
    rel = project_config_relpath(tool)
    if rel is None:
        return None
    project_path = project_root / rel
    template = bundled_template_path(tool)
    template_text = template.read_text(encoding="utf-8") if template.is_file() else ""
    project_text = project_path.read_text(encoding="utf-8") if project_path.is_file() else ""
    if project_text == template_text:
        return None
    return "".join(
        difflib.unified_diff(
            template_text.splitlines(keepends=True),
            project_text.splitlines(keepends=True),
            fromfile=f"bundled/{tool.configuration.bundled}",
            tofile=str(rel),
        )
    )


def diff_configs(
    project_root: Path,
    catalog: Catalog,
    *,
    tool_id: str | None = None,
) -> str:
    if tool_id is not None:
        tools = [catalog.get_tool(tool_id)]
    else:
        tools = [tool for tool in catalog.tools.values() if tool.configuration.bundled]

    chunks = [chunk for tool in tools if (chunk := diff_tool_config(project_root, tool))]
    if not chunks:
        return "no differences\n"
    return "\n".join(chunks)
