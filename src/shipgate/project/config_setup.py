"""Scaffold project tool configs from bundled templates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.gates.paths import bundled_root_path
from shipgate.paths import (
    POLICY_CACHE_KEY,
    PROJECT_GATE_CONFIGS_DIR,
    PROJECT_ROOT_CACHE_KEY,
    update_project_cache_env,
)
from shipgate.project.layout import detect_layout
from shipgate.project.scope_defaults import (
    render_scopes_toml,
    render_scopes_yaml,
    replace_pyproject_scopes,
    replace_yaml_scopes,
)

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog, ToolDefinition

ROOT_PACKAGE_PLACEHOLDER = "__ROOT_PACKAGE__"
PYPROJECT_TOML = "pyproject.toml"


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


def detect_importable_root_package(project_root: Path) -> str | None:
    """Importable src-layout package name for import-linter / deptry scaffolding."""
    return RootPackageDetector(project_root).from_src_layout()


class RootPackageDetector:
    def __init__(self, project_root: Path) -> None:
        self.root = project_root.resolve()

    def from_src_layout(self) -> str | None:
        src = self.root / "src"
        if not src.is_dir():
            return None
        packages = sorted(
            path.name
            for path in src.iterdir()
            if path.is_dir() and not path.name.startswith(".") and (path / "__init__.py").is_file()
        )
        return packages[0] if packages else None


def render_root_package_template(text: str, root_package: str) -> str:
    return text.replace(ROOT_PACKAGE_PLACEHOLDER, root_package)


def scaffold_file_if_missing(
    project_root: Path,
    relative_path: Path,
    *,
    bundled_template: Path,
    root_package: str | None = None,
) -> Path | None:
    """Copy a bundled template when the project target path is missing."""
    target = project_root / relative_path
    if target.is_file():
        return None
    if not bundled_template.is_file():
        msg = f"bundled config template not found: {bundled_template}"
        raise FileNotFoundError(msg)
    content = bundled_template.read_text(encoding="utf-8")
    if ROOT_PACKAGE_PLACEHOLDER in content:
        if root_package is None:
            # Do not write a broken import-linter (or similar) contract.
            return None
        content = render_root_package_template(content, root_package)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def ensure_minimal_pyproject(project_root: Path) -> Path | None:
    """Create a starter pyproject.toml so packaging tools have project metadata."""
    pyproject = project_root / PYPROJECT_TOML
    if pyproject.is_file():
        return None
    name = re.sub(r"[^A-Za-z0-9._-]", "-", project_root.name).strip("-._") or "project"
    pyproject.write_text(
        f'[project]\nname = "{name}"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    return pyproject


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


def read_pyproject_shipgate_template(project_root: Path | None = None) -> str:
    bundled = bundled_pyproject_shipgate_template()
    if not bundled.is_file():
        msg = f"bundled pyproject shipgate template not found: {bundled}"
        raise FileNotFoundError(msg)
    text = bundled.read_text(encoding="utf-8")
    if project_root is None:
        return text
    return replace_pyproject_scopes(text, render_scopes_toml(detect_layout(project_root)))


def bundled_deptry_pyproject_template() -> Path:
    return bundled_root_path() / "setup" / "deptry-pyproject.toml"


def read_deptry_pyproject_template() -> str:
    bundled = bundled_deptry_pyproject_template()
    if not bundled.is_file():
        msg = f"bundled deptry pyproject template not found: {bundled}"
        raise FileNotFoundError(msg)
    return bundled.read_text(encoding="utf-8")


def ensure_deptry_pyproject_section(project_root: Path) -> Path | None:
    """Append a starter [tool.deptry] section when pyproject.toml lacks one."""
    pyproject = project_root / PYPROJECT_TOML
    if not pyproject.is_file():
        return None
    content = pyproject.read_text(encoding="utf-8")
    if "[tool.deptry]" in content:
        return None
    if content and not content.endswith("\n"):
        content += "\n"
    section = read_deptry_pyproject_template()
    root_package = detect_importable_root_package(project_root)
    if root_package is not None:
        section = section.replace(
            '# known_first_party = ["your_package"]',
            f'known_first_party = ["{root_package}"]',
        )
    pyproject.write_text(content + "\n" + section, encoding="utf-8")
    return pyproject


def bundled_shipgate_yaml_template() -> Path:
    return bundled_root_path() / "setup" / "shipgate.yaml"


def read_shipgate_yaml_template(project_root: Path | None = None) -> str:
    bundled = bundled_shipgate_yaml_template()
    if not bundled.is_file():
        msg = f"bundled shipgate.yaml template not found: {bundled}"
        raise FileNotFoundError(msg)
    text = bundled.read_text(encoding="utf-8")
    if project_root is None:
        return text
    return replace_yaml_scopes(text, render_scopes_yaml(detect_layout(project_root)))


def scaffold_bundled_configs(project_root: Path, catalog: Catalog) -> list[Path]:
    """Copy missing tool configs from bundled templates; deduplicate shared configs."""
    root = project_root.resolve()
    created: list[Path] = []
    seen: set[Path] = set()
    # Only substitute import-linter placeholders when a real src package exists.
    importable_package = detect_importable_root_package(root)
    for tool in catalog.tools.values():
        rel = project_config_relpath(tool)
        if rel is None or rel in seen:
            continue
        seen.add(rel)
        result = scaffold_file_if_missing(
            root,
            rel,
            bundled_template=bundled_template_path(tool),
            root_package=importable_package,
        )
        if result is not None:
            created.append(result)
    deptry = ensure_deptry_pyproject_section(root)
    if deptry is not None:
        created.append(deptry)
    return created
