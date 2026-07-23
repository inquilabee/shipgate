"""Gate initialization."""

from pathlib import Path

from shipgate.gates.paths import gate_init_template_path
from shipgate.paths import PROJECT_GATES_DIR


def init_gate(project_root: Path, name: str) -> Path:
    gates_dir = project_root / PROJECT_GATES_DIR
    gates_dir.mkdir(parents=True, exist_ok=True)
    path = gates_dir / f"{name}.sh"
    if not path.exists():
        path.write_text(gate_init_template_path().read_text(encoding="utf-8"), encoding="utf-8")
        path.chmod(0o755)
    return path
