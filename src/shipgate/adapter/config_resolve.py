"""Config path resolution for adapter."""

from pathlib import Path

from shipgate.domain.catalog import ToolDefinition
from shipgate.domain.project import ProjectConfig


def resolve_config_paths(
    tool: ToolDefinition,
    project: ProjectConfig,
    project_root: Path,
) -> tuple[Path, ...]:
    if project.config_mode == "bundled" and tool.configuration.bundled:
        bundled = Path(__file__).resolve().parents[1] / "catalog" / "bundled"
        return (bundled / tool.configuration.bundled,)
    if project.config_mode == "repo":
        discovered: list[Path] = []
        for pattern in tool.configuration.discover:
            candidate = project_root / pattern
            if candidate.is_file():
                discovered.append(candidate)
        return tuple(discovered)
    discovered = []
    for pattern in tool.configuration.discover:
        candidate = project_root / pattern
        if candidate.is_file():
            discovered.append(candidate)
    if not discovered and tool.configuration.bundled:
        bundled = Path(__file__).resolve().parents[1] / "catalog" / "bundled"
        discovered.append(bundled / tool.configuration.bundled)
    return tuple(discovered)
