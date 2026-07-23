"""Project initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import load_catalog
from shipgate.errors import ShipGateError
from shipgate.gates.setup import setup_bundled_gates
from shipgate.paths import project_root_cache_env_path, shipgate_dir, shipgate_yaml_path
from shipgate.project.catalog import sync_catalog
from shipgate.project.config_setup import (
    read_pyproject_shipgate_template,
    read_shipgate_yaml_template,
    scaffold_bundled_configs,
    scaffold_shipgate_gitignore,
    write_project_root_cache,
)
from shipgate.runtime.project_python import (
    discover_and_persist_project_python,
    persist_project_python,
)

if TYPE_CHECKING:
    from pathlib import Path

INIT_MODES = frozenset({"yaml", "pyproject"})


def scaffold_project_layout(
    project_root: Path,
    *,
    policy: str = "yaml",
    project_env: Path | None = None,
) -> list[Path]:
    """Create .shipgate/ directories and copy missing bundled configs."""
    root = project_root.resolve()
    catalog = load_catalog()
    (shipgate_dir(root) / "reports").mkdir(parents=True, exist_ok=True)
    (shipgate_dir(root) / "gates").mkdir(parents=True, exist_ok=True)
    (shipgate_dir(root) / "configs").mkdir(parents=True, exist_ok=True)
    created = scaffold_bundled_configs(root, catalog)
    created.extend(sync_catalog(root))
    gitignore = scaffold_shipgate_gitignore(root)
    if gitignore is not None:
        created.append(gitignore)
    setup_bundled_gates(root, catalog)
    created.append(write_project_root_cache(root, policy=policy))
    if project_env is not None:
        persist_project_python(root, project_env)
    else:
        discovered = discover_and_persist_project_python(root)
        if discovered is not None:
            created.append(project_root_cache_env_path(root))
    return created


def init_project(
    project_root: Path,
    *,
    configs_only: bool = False,
    mode: str = "yaml",
    project_env: Path | None = None,
) -> Path | None:
    """Create ShipGate policy and .shipgate/ scaffolding at the project root."""
    if mode not in INIT_MODES:
        msg = f"invalid init mode: {mode!r}; expected one of {sorted(INIT_MODES)}"
        raise ShipGateError(msg)
    root = project_root.resolve()
    if configs_only:
        scaffold_project_layout(root, policy=mode, project_env=project_env)
        return None
    if mode == "pyproject":
        return ProjectInitializer.init_pyproject_policy(root, project_env=project_env)
    return ProjectInitializer.init_yaml_policy(root, project_env=project_env)


class ProjectInitializer:
    @staticmethod
    def init_yaml_policy(root: Path, *, project_env: Path | None = None) -> Path:
        config_path = shipgate_yaml_path(root)
        if config_path.is_file():
            raise ShipGateError(f"shipgate.yaml already exists: {config_path}")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(read_shipgate_yaml_template(), encoding="utf-8")
        scaffold_project_layout(root, policy="yaml", project_env=project_env)
        return config_path

    @staticmethod
    def init_pyproject_policy(root: Path, *, project_env: Path | None = None) -> Path:
        pyproject_path = root / "pyproject.toml"
        if not pyproject_path.is_file():
            pyproject_path.write_text(
                '[project]\nname = "project"\nversion = "0.1.0"\n',
                encoding="utf-8",
            )
        content = pyproject_path.read_text(encoding="utf-8")
        if "[tool.shipgate]" in content:
            raise ShipGateError(f"[tool.shipgate] already exists in {pyproject_path}")
        if content and not content.endswith("\n"):
            content += "\n"
        content += read_pyproject_shipgate_template()
        pyproject_path.write_text(content, encoding="utf-8")
        scaffold_project_layout(root, policy="pyproject", project_env=project_env)
        return pyproject_path
