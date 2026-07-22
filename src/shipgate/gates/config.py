"""Gate configuration loading and environment mapping."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from shipgate.gates.paths import bundled_root_path

if TYPE_CHECKING:
    from shipgate.domain.catalog import ToolDefinition
    from shipgate.domain.project import ProjectConfig


def load_bundled_gate_config(tool: ToolDefinition) -> dict[str, Any]:
    """Load the bundled default YAML config for a gate tool."""
    if not tool.configuration.bundled:
        return {}
    bundled = bundled_root_path() / tool.configuration.bundled
    if not bundled.is_file():
        return {}
    data = yaml.safe_load(bundled.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        msg = f"Gate config must be a mapping: {bundled}"
        raise ValueError(msg)
    return dict(data)


def load_gate_config(
    tool: ToolDefinition,
    project_root: Path,
    project: ProjectConfig | None,
    *,
    config_paths: tuple[Path, ...],
) -> dict[str, Any]:
    config_path = resolve_gate_config_path(tool, project_root, project, config_paths)
    if config_path is None or not config_path.is_file():
        return {}
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        msg = f"Gate config must be a mapping: {config_path}"
        raise ValueError(msg)
    config = dict(data)
    resolve_allowlist_path(project_root, config)
    return config


def write_resolved_gate_config(
    check_id: str,
    project_root: Path,
    config: dict[str, Any],
) -> Path:
    cache_dir = project_root / ".shipgate" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    resolved = cache_dir / f"{check_id}.config.yaml"
    resolved.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    return resolved


def gate_env_from_config(config: dict[str, Any], project_root: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for key, value in config.items():
        if value is None:
            continue
        env[f"GATE_{key.upper()}"] = gate_env_value(value)
    allowlist = config.get("allowlist_file")
    if allowlist:
        path = Path(str(allowlist))
        if not path.is_absolute():
            path = project_root / path
        env["GATE_ALLOWLIST_FILE"] = str(path.resolve())
    return env


def resolve_gate_config_path(
    tool: ToolDefinition,
    project_root: Path,
    project: ProjectConfig | None,
    config_paths: tuple[Path, ...],
) -> Path | None:
    for candidate in config_paths:
        if candidate.is_file():
            return candidate
    for convention in (
        project_root / f"{tool.id}.yaml",
        project_root / ".shipgate" / "configs" / "gates" / f"{tool.id}.yaml",
    ):
        if convention.is_file():
            return convention
    if tool.configuration.bundled:
        bundled = bundled_root_path() / tool.configuration.bundled
        if bundled.is_file():
            return bundled
    return None


def resolve_allowlist_path(project_root: Path, config: dict[str, Any]) -> None:
    raw = config.get("allowlist_file")
    if not raw:
        return
    path = Path(str(raw))
    if not path.is_absolute():
        path = project_root / path
    if path.is_file():
        config["allowlist_file"] = str(path.resolve())


def gate_env_value(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
