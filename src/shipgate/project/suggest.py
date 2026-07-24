"""Additive tool suggestions for project init."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog


def suggest_tools(project_root: Path, catalog: Catalog) -> list[str]:
    return InitToolSuggestions.collect(project_root, catalog)


class InitToolSuggestions:
    @staticmethod
    def collect(project_root: Path, catalog: Catalog) -> list[str]:
        root = project_root.resolve()
        lines: list[str] = []
        for tool_id, tool in sorted(catalog.tools.items()):
            if tool.suggest_if is None or not tool.suggest_if.files_present:
                continue
            if not InitToolSuggestions.matches_files_present(root, tool.suggest_if.files_present):
                continue
            lines.append(InitToolSuggestions.suggestion_line(tool_id))
        return lines

    @staticmethod
    def matches_files_present(project_root: Path, patterns: tuple[str, ...]) -> bool:
        return any(any(project_root.glob(pattern)) for pattern in patterns)

    @staticmethod
    def suggestion_line(tool_id: str) -> str:
        suite_hint = ""
        if tool_id == "hadolint.check":
            suite_hint = " (suite: docker)"
        return f"suggest: {tool_id} matches project files{suite_hint}"
