"""Shared gate config loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from shipgate.policy.core.path_allowlist import PathAllowlist


def load_gate_mapping(config_path: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(config, dict):
        msg = f"Gate config must be a mapping: {config_path}"
        raise ValueError(msg)
    return config


def resolve_config_allowlist(root: Path, config: dict[str, Any]) -> Path | None:
    allowlist_file = config.get("allowlist_file")
    if not allowlist_file:
        return None
    allowlist_path = Path(str(allowlist_file))
    if not allowlist_path.is_absolute():
        allowlist_path = root / allowlist_path
    return allowlist_path


def load_allowlist_paths(path: Path | None) -> set[str]:
    if path is None:
        return set()
    return set(PathAllowlist(path).paths())
