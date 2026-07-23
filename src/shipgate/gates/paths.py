"""Bundled gate path helpers."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition


def bundled_root_path() -> Path:
    return Path(str(resources.files("shipgate.catalog.bundled")))


def gates_lib_path() -> Path:
    return bundled_root_path() / "gates" / "lib.sh"


def gate_init_template_path() -> Path:
    return Path(str(resources.files("shipgate.gates.templates") / "gate.sh"))


def resolve_gate_script(tool: ToolDefinition, project_root: Path) -> Path:
    if tool.script:
        script = Path(tool.script)
        if script.is_absolute():
            return script
        return bundled_root_path() / script
    script_path = Path(tool.executable)
    if script_path.is_absolute():
        return script_path
    return (project_root / script_path).resolve()
