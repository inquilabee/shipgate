"""Additive tool suggestions for project init."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.core.files_present import any_files_present

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog


def suggest_tools(project_root: Path, catalog: Catalog) -> list[str]:
    return InitToolSuggestions(project_root, catalog).collect()


class InitToolSuggestions:
    def __init__(self, project_root: Path, catalog: Catalog) -> None:
        self.root = project_root.resolve()
        self.catalog = catalog

    def collect(self) -> list[str]:
        lines: list[str] = []
        for tool_id, tool in sorted(self.catalog.tools.items()):
            if tool.suggest_if is None or not tool.suggest_if.files_present:
                continue
            if not any_files_present(self.root, tool.suggest_if.files_present):
                continue
            lines.append(self.suggestion_line(tool_id))
        return lines

    def suggestion_line(self, tool_id: str) -> str:
        _ = self
        suite_hint = " (suite: docker)" if tool_id == "hadolint.check" else ""
        return f"suggest: {tool_id} matches project files{suite_hint}"
