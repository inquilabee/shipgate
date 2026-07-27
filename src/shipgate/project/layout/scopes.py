"""Render and splice named scope fragments for shipgate init."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.project.layout.types import ProjectLayout

SCOPES_PREFIX = "[tool.shipgate.scopes."
ALLOWLISTS_HEADER = "[tool.shipgate.allowlists]"
ScopeBody = dict[str, object]


class ScopeFragments:
    """Build YAML/TOML scope blocks from one detected layout."""

    def __init__(self, layout: ProjectLayout) -> None:
        self.layout = layout

    def default_scopes(self) -> dict[str, ScopeBody]:
        scopes: dict[str, ScopeBody] = {"semgrep": {"target": "."}}
        if self.layout.python_dirs:
            scopes["python-src"] = self.scope_dirs(self.layout.python_dirs)
        if self.layout.test_dirs:
            scopes["python-test-src"] = self.scope_dirs(self.layout.test_dirs)
        if self.layout.docs_dirs:
            scopes["docs"] = self.scope_dirs(self.layout.docs_dirs)
        return scopes

    def scope_dirs(self, dirs: tuple[str, ...]) -> ScopeBody:
        _ = self
        if len(dirs) == 1:
            return {"target": dirs[0]}
        return {"target": ".", "include": list(dirs)}

    def render_yaml(self) -> str:
        lines = ["scopes:"]
        for name, body in self.default_scopes().items():
            lines.append(f"  {name}:")
            prefix = "    "
            lines.append(f"{prefix}target: {body['target']}")
            include = body.get("include")
            if isinstance(include, list) and include:
                lines.append(f"{prefix}include:")
                lines.extend(f"{prefix}  - {item}" for item in include)
        return "\n".join(lines) + "\n"

    def render_toml(self) -> str:
        blocks: list[str] = []
        for name, body in self.default_scopes().items():
            lines = [f"{SCOPES_PREFIX}{name}]", f'target = "{body["target"]}"']
            include = body.get("include")
            if isinstance(include, list) and include:
                joined = ", ".join(f'"{item}"' for item in include)
                lines.append(f"include = [{joined}]")
            blocks.append("\n".join(lines))
        return "\n\n".join(blocks) + "\n"


class ScopeTemplateSplicer:
    """Replace scope sections inside init policy templates."""

    def __init__(self, template: str) -> None:
        self.template = template

    def replace_yaml(self, scopes_block: str) -> str:
        lines = self.template.splitlines(keepends=True)
        start = next(
            (i for i, line in enumerate(lines) if line in {"scopes:\n", "scopes:"}),
            None,
        )
        if start is None:
            return self.template.rstrip("\n") + "\n" + scopes_block
        end = start + 1
        while end < len(lines) and (lines[end].startswith((" ", "\t")) or lines[end].strip() == ""):
            end += 1
        block = scopes_block if scopes_block.endswith("\n") else scopes_block + "\n"
        return "".join(lines[:start]) + block + "".join(lines[end:])

    def replace_toml(self, scopes_block: str) -> str:
        lines = self.template.splitlines(keepends=True)
        block = scopes_block if scopes_block.endswith("\n") else scopes_block + "\n"
        start = next((i for i, line in enumerate(lines) if line.startswith(SCOPES_PREFIX)), None)
        if start is None:
            return self.insert_toml(lines, block)
        end = self.toml_end(lines, start)
        padded = block if block.endswith("\n\n") else block.rstrip("\n") + "\n\n"
        return "".join(lines[:start]) + padded + "".join(lines[end:])

    def toml_end(self, lines: list[str], start: int) -> int:
        _ = self
        end = start
        while end < len(lines):
            line = lines[end]
            if end > start and line.startswith("[") and not line.startswith(SCOPES_PREFIX):
                break
            end += 1
        return end

    def insert_toml(self, lines: list[str], block: str) -> str:
        allow = next(
            (i for i, line in enumerate(lines) if line.startswith(ALLOWLISTS_HEADER)),
            None,
        )
        if allow is None:
            return self.template.rstrip("\n") + "\n\n" + block
        return "".join(lines[:allow]) + block + "\n" + "".join(lines[allow:])
