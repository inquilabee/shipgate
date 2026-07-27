"""Project initialization."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.catalog.loader import CatalogLoader
from shipgate.errors import ShipGateError
from shipgate.gates.setup import setup_bundled_gates
from shipgate.paths import (
    PROJECT_CACHE_ENV,
    PROJECT_CONFIGS_DIR,
    PROJECT_GATES_DIR,
    PROJECT_REPORTS_DIR,
    SHIPGATE_YAML,
)
from shipgate.project.catalog import sync_catalog
from shipgate.project.config_setup import (
    ensure_minimal_pyproject,
    read_pyproject_shipgate_template,
    read_shipgate_yaml_template,
    scaffold_bundled_configs,
    scaffold_shipgate_gitignore,
    write_project_root_cache,
)
from shipgate.project.python import (
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
    catalog = CatalogLoader.load()
    (root / PROJECT_REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    (root / PROJECT_GATES_DIR).mkdir(parents=True, exist_ok=True)
    (root / PROJECT_CONFIGS_DIR).mkdir(parents=True, exist_ok=True)
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
            created.append(root / PROJECT_CACHE_ENV)
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
        return ProjectInitializer(root, project_env=project_env).init_pyproject_policy()
    return ProjectInitializer(root, project_env=project_env).init_yaml_policy()


class ProjectInitializer:
    def __init__(self, root: Path, *, project_env: Path | None = None) -> None:
        self.root = root
        self.project_env = project_env

    def init_yaml_policy(self) -> Path:
        config_path = self.root / SHIPGATE_YAML
        if config_path.is_file():
            raise ShipGateError(f"shipgate.yaml already exists: {config_path}")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(read_shipgate_yaml_template(self.root), encoding="utf-8")
        # Packaging tools (deptry, pip-audit) need project metadata.
        ensure_minimal_pyproject(self.root)
        scaffold_project_layout(self.root, policy="yaml", project_env=self.project_env)
        return config_path

    def init_pyproject_policy(self) -> Path:
        pyproject_path = self.root / "pyproject.toml"
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
        content += read_pyproject_shipgate_template(self.root)
        pyproject_path.write_text(content, encoding="utf-8")
        scaffold_project_layout(self.root, policy="pyproject", project_env=self.project_env)
        return pyproject_path
