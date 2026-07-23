"""Bundled gate path helpers."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import PlanningError
from shipgate.paths import PROJECT_GATES_DIR

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition


def bundled_root_path() -> Path:
    return Path(str(resources.files("shipgate.catalog.bundled")))


def gates_lib_path() -> Path:
    return bundled_root_path() / "gates" / "lib.sh"


def gate_init_template_path() -> Path:
    return Path(str(resources.files("shipgate.gates.templates") / "gate.sh"))


def resolve_gate_script(tool: ToolDefinition, project_root: Path) -> Path:
    project_root = project_root.resolve()
    project_gates = (project_root / PROJECT_GATES_DIR).resolve()
    bundled_gates = (bundled_root_path() / "gates").resolve()

    if tool.script:
        script = Path(tool.script)
        candidate = script if script.is_absolute() else (bundled_root_path() / script)
        return require_under(candidate.resolve(), (bundled_gates, project_gates))

    script_path = Path(tool.executable)
    if script_path.is_absolute():
        return require_under(script_path.resolve(), (bundled_gates, project_gates))
    return require_under((project_root / script_path).resolve(), (project_gates,))


def require_under(path: Path, roots: tuple[Path, ...]) -> Path:
    for root in roots:
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file():
            return path
    raise PlanningError(
        f"gate script not allowed: {path}",
        hint="scripts must live under .shipgate/gates/ or bundled gates/",
    )
