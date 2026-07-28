"""Scaffold project files declared in gate bundled configs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.gates.paths import bundled_root_path

if TYPE_CHECKING:
    from collections.abc import Mapping


def scaffold_file(
    project_root: Path,
    relative_path: str | Path,
    *,
    bundled_template: str | Path,
    create_parents: bool = True,
) -> Path:
    """Copy a bundled template into the project when the target path is missing."""
    target = Path(relative_path)
    target = target if target.is_absolute() else project_root / target
    if target.is_file():
        return target
    template = bundled_root_path() / bundled_template
    if not template.is_file():
        msg = f"gate setup template not found: {template}"
        raise FileNotFoundError(msg)
    if create_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(template.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def scaffold_from_gate_config(project_root: Path, config: Mapping[str, object]) -> None:
    """Scaffold allowlist_file from bundled setup templates when missing."""
    raw = config.get("allowlist_file")
    if not raw:
        return
    rel = Path(str(raw))
    template = bundled_root_path() / "setup" / "allowlists" / rel.name
    if not template.is_file():
        return
    scaffold_file(project_root, rel, bundled_template=template)
