"""Scaffold project tool configs from bundled templates."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.gates.paths import bundled_root_path
from shipgate.paths import (
    POLICY_CACHE_KEY,
    PROJECT_GATE_CONFIGS_DIR,
    PROJECT_ROOT_CACHE_KEY,
    update_project_cache_env,
)

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog, ToolDefinition


def project_config_relpath(tool: ToolDefinition) -> Path | None:
    """Relative project path for a tool's scaffolded config file."""
    bundled = tool.configuration.bundled
    if not bundled:
        return None
    bundled_path = Path(bundled)
    is_gate = (
        len(bundled_path.parts) >= 2
        and bundled_path.parts[0] == "configs"
        and bundled_path.parts[1] == "gates"
    )
    if is_gate:
        return PROJECT_GATE_CONFIGS_DIR / f"{tool.id}.yaml"
    if bundled_path.name == "mdformat.toml":
        return Path(".mdformat.toml")
    return Path(".shipgate/configs") / bundled_path.name


def bundled_template_path(tool: ToolDefinition) -> Path:
    if not tool.configuration.bundled:
        msg = f"tool {tool.id!r} has no bundled config"
        raise ValueError(msg)
    return bundled_root_path() / tool.configuration.bundled


def scaffold_file_if_missing(
    project_root: Path,
    relative_path: Path,
    *,
    bundled_template: Path,
) -> Path | None:
    """Copy a bundled template when the project target path is missing."""
    target = project_root / relative_path
    if target.is_file():
        return None
    if not bundled_template.is_file():
        msg = f"bundled config template not found: {bundled_template}"
        raise FileNotFoundError(msg)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(bundled_template.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def scaffold_shipgate_gitignore(project_root: Path) -> Path | None:
    """Copy bundled .shipgate/.gitignore when missing."""
    bundled = bundled_root_path() / "setup" / ".gitignore"
    return scaffold_file_if_missing(
        project_root,
        Path(".shipgate/.gitignore"),
        bundled_template=bundled,
    )


def write_project_root_cache(project_root: Path, *, policy: str = "yaml") -> Path:
    """Record the project root and policy mode from ``shipgate init``."""
    root = project_root.resolve()
    return update_project_cache_env(
        root,
        {
            PROJECT_ROOT_CACHE_KEY: str(root),
            POLICY_CACHE_KEY: policy,
        },
    )


def bundled_pyproject_shipgate_template() -> Path:
    return bundled_root_path() / "setup" / "pyproject-shipgate.toml"


def read_pyproject_shipgate_template() -> str:
    bundled = bundled_pyproject_shipgate_template()
    if not bundled.is_file():
        msg = f"bundled pyproject shipgate template not found: {bundled}"
        raise FileNotFoundError(msg)
    return bundled.read_text(encoding="utf-8")


def bundled_shipgate_yaml_template() -> Path:
    return bundled_root_path() / "setup" / "shipgate.yaml"


def read_shipgate_yaml_template() -> str:
    bundled = bundled_shipgate_yaml_template()
    if not bundled.is_file():
        msg = f"bundled shipgate.yaml template not found: {bundled}"
        raise FileNotFoundError(msg)
    return bundled.read_text(encoding="utf-8")


def scaffold_bundled_configs(project_root: Path, catalog: Catalog) -> list[Path]:
    """Copy missing tool configs from bundled templates; deduplicate shared configs."""
    root = project_root.resolve()
    created: list[Path] = []
    seen: set[Path] = set()
    for tool in catalog.tools.values():
        rel = project_config_relpath(tool)
        if rel is None or rel in seen:
            continue
        seen.add(rel)
        result = scaffold_file_if_missing(
            root,
            rel,
            bundled_template=bundled_template_path(tool),
        )
        if result is not None:
            created.append(result)
    return created
