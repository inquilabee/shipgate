"""Config file discovery."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.paths import LEGACY_CONFIG_FILENAMES, SHIPGATE_YAML

if TYPE_CHECKING:
    from pathlib import Path


def discover_yaml_config_path(project_root: Path, explicit: Path | None = None) -> Path | None:
    """Discover a YAML policy file, preferring `.shipgate/shipgate.yaml`."""
    if explicit is not None:
        return explicit.resolve()
    canonical = project_root / SHIPGATE_YAML
    if canonical.is_file():
        return canonical.resolve()
    for name in LEGACY_CONFIG_FILENAMES:
        candidate = project_root / name
        if candidate.is_file():
            return candidate.resolve()
    return None


def discover_config_path(project_root: Path, explicit: Path | None = None) -> Path | None:
    """Backward-compatible alias for YAML discovery."""
    return discover_yaml_config_path(project_root, explicit)
