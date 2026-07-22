"""Gate initialization."""

from pathlib import Path

GATE_TEMPLATE = """#!/usr/bin/env bash
set -euo pipefail

# shellcheck source=/dev/null
source "$(shipgate gates lib-path)"

gate_init "gate"

# Example: fail when scan target is missing
if [[ ! -d "${SHIPGATE_TARGET:-.}" ]]; then
\tgate_fail "missing-target" "Scan target not found: ${SHIPGATE_TARGET:-.}"
fi

gate_finish
"""


def init_gate(project_root: Path, name: str) -> Path:
    gates_dir = project_root / ".shipgate" / "gates"
    gates_dir.mkdir(parents=True, exist_ok=True)
    path = gates_dir / f"{name}.sh"
    if not path.exists():
        path.write_text(GATE_TEMPLATE, encoding="utf-8")
        path.chmod(0o755)
    return path
