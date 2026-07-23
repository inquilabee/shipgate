"""Gate initialization."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from shipgate.errors import ConfigError
from shipgate.gates.paths import gate_init_template_path
from shipgate.paths import PROJECT_GATES_DIR

if TYPE_CHECKING:
    from pathlib import Path

GATE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def validate_gate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or not GATE_NAME_PATTERN.fullmatch(cleaned):
        raise ConfigError(
            f"invalid gate name {name!r}",
            hint="use a simple name like 'my-gate' (letters, digits, ., _, -)",
        )
    if ".." in cleaned:
        raise ConfigError(
            f"invalid gate name {name!r}",
            hint="gate names must not contain '..'",
        )
    return cleaned


def init_gate(project_root: Path, name: str) -> Path:
    safe_name = validate_gate_name(name)
    gates_dir = (project_root / PROJECT_GATES_DIR).resolve()
    gates_dir.mkdir(parents=True, exist_ok=True)
    path = (gates_dir / f"{safe_name}.sh").resolve()
    try:
        path.relative_to(gates_dir)
    except ValueError as exc:
        raise ConfigError(
            f"gate path escapes gates directory: {path}",
            path=str(path),
        ) from exc
    if not path.exists():
        path.write_text(gate_init_template_path().read_text(encoding="utf-8"), encoding="utf-8")
        path.chmod(0o755)
    return path
