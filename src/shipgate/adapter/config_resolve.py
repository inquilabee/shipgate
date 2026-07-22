"""Config path resolution for adapter."""

from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.project import ProjectConfig


def bundled_configs_root() -> Path:
    return Path(__file__).resolve().parents[1] / "catalog" / "bundled"


def resolve_config_paths(
    tool: ToolDefinition,
    project: ProjectConfig,
    project_root: Path,
) -> tuple[Path, ...]:
    bundled = bundled_configs_root()
    if project.config_mode == "bundled" and tool.configuration.bundled:
        return (bundled / tool.configuration.bundled,)
    for pattern in tool.configuration.discover:
        candidate = project_root / pattern
        if candidate.is_file():
            return (candidate,)
    if project.config_mode == "auto" and tool.configuration.bundled:
        return (bundled / tool.configuration.bundled,)
    return ()
