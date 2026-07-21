"""Gate initialization."""

from pathlib import Path

GATE_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail
echo "gate passed"
"""


def init_gate(project_root: Path, name: str) -> Path:
    gates_dir = project_root / ".shipgate" / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    path = gates_dir / f"{name}.sh"
    if not path.exists():
        path.write_text(GATE_TEMPLATE, encoding="utf-8")
        path.chmod(0o755)
    return path
