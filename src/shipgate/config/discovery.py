"""Config file discovery."""

from pathlib import Path

CONFIG_FILENAMES = ("shipgate.yaml", ".shipgate.yaml")


def discover_config_path(project_root: Path, explicit: Path | None = None) -> Path | None:
    if explicit is not None:
        return explicit.resolve()
    for name in CONFIG_FILENAMES:
        candidate = project_root / name
        if candidate.is_file():
            return candidate.resolve()
    return None
