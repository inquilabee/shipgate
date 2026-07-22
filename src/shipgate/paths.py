"""Project and report path helpers."""

from __future__ import annotations

from pathlib import Path

PROJECT_SERVER_DIR = ".shipgate/server"
PROJECT_WORKTREES_DIR = ".shipgate/worktrees"
SERVER_DB_FILENAME = "report.db"


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward from start to find a project root (shipgate.yaml, .git, or pyproject.toml)."""
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "shipgate.yaml").is_file():
            return candidate
        if (candidate / ".shipgate.yaml").is_file():
            return candidate
        if (candidate / ".git").exists():
            return candidate
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return current


def shipgate_dir(project_root: Path) -> Path:
    return project_root / ".shipgate"


def reports_root(project_root: Path) -> Path:
    return shipgate_dir(project_root) / "reports"


def raw_reports_dir(project_root: Path, run_id: str) -> Path:
    return reports_root(project_root) / "raw" / run_id


def failure_report_dir(project_root: Path, run_id: str) -> Path:
    return reports_root(project_root) / "failures" / run_id


def tools_dir(project_root: Path) -> Path:
    return shipgate_dir(project_root) / "tools"


def managed_bin_dir(project_root: Path) -> Path:
    return tools_dir(project_root) / "bin"


def managed_python_env(project_root: Path) -> Path:
    return tools_dir(project_root) / "python"


def server_dir(project_root: Path) -> Path:
    return project_root / PROJECT_SERVER_DIR


def normalize_finding_path(
    path: str | None,
    *,
    project_root: Path | None = None,
) -> str | None:
    if not path:
        return None
    normalized = path.replace("\\", "/")
    if project_root is not None:
        try:
            rel = Path(normalized).resolve().relative_to(project_root.resolve())
            return rel.as_posix()
        except ValueError:
            pass
    if normalized.startswith("./"):
        return normalized[2:]
    return normalized
