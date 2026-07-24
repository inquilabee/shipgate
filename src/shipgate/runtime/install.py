"""Managed tool installation."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.paths import PROJECT_TOOLS_DIR
from shipgate.planning.core.suites import expand_suite
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.installers.registry import get_installer
from shipgate.runtime.lockfile import write_lockfile

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, InstallDefinition

MANIFEST_SCHEMA = "shipgate.install.v1"


def collect_install_requirements(
    suite_id: str,
    catalog: Catalog,
) -> tuple[dict[str, InstallDefinition], dict[str, InstallDefinition]]:
    tool_ids = list(expand_suite(suite_id, catalog))
    if suite_id != "format":
        seen = set(tool_ids)
        for tool_id in expand_suite("format", catalog):
            if tool_id not in seen:
                tool_ids.append(tool_id)
                seen.add(tool_id)
    return collect_install_requirements_for_tools(tool_ids, catalog)


def collect_install_requirements_for_tools(
    tool_ids: list[str],
    catalog: Catalog,
) -> tuple[dict[str, InstallDefinition], dict[str, InstallDefinition]]:
    python_packages: dict[str, InstallDefinition] = {}
    binary_packages: dict[str, InstallDefinition] = {}
    for tool_id in tool_ids:
        tool = catalog.get_tool(tool_id)
        if not tool.install:
            continue
        if tool.install.manager == "python":
            python_packages[tool.install.package] = tool.install
        elif tool.install.manager == "binary":
            key = tool.install.binary or tool.install.package
            binary_packages[key] = tool.install
    return python_packages, binary_packages


def write_manifest(
    project_root: Path,
    *,
    python_packages: dict[str, InstallDefinition],
    binary_packages: dict[str, InstallDefinition],
) -> Path:
    manifest = read_manifest(project_root)
    manifest.update(
        {
            "schema_version": MANIFEST_SCHEMA,
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "packages": {
                **manifest.get("packages", {}),
                **{
                    pkg: install_def.version or "latest"
                    for pkg, install_def in python_packages.items()
                },
            },
            "binaries": {
                **manifest.get("binaries", {}),
                **{
                    name: install_def.version or "latest"
                    for name, install_def in binary_packages.items()
                },
            },
        }
    )
    manifest_path = tools_manifest_path(project_root)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def write_install_lockfile(
    project_root: Path,
    *,
    python_packages: dict[str, InstallDefinition],
    binary_packages: dict[str, InstallDefinition],
) -> Path:
    packages = {
        **{name: install_def.version for name, install_def in python_packages.items()},
        **{name: install_def.version for name, install_def in binary_packages.items()},
    }
    lock_path = project_root / ".shipgate" / "lock.json"
    write_lockfile(lock_path, packages)
    return lock_path


def install_suite(
    project_root: Path,
    suite_id: str,
    catalog: Catalog,
    *,
    force: bool = False,
) -> Path:
    python_packages, binary_packages = collect_install_requirements(suite_id, catalog)
    (project_root / PROJECT_TOOLS_DIR).mkdir(parents=True, exist_ok=True)
    if python_packages:
        get_installer("python").install_packages(project_root, python_packages, force=force)
    manifest_path = write_manifest(
        project_root,
        python_packages=python_packages,
        binary_packages={},
    )
    if not binary_packages:
        write_install_lockfile(
            project_root,
            python_packages=python_packages,
            binary_packages={},
        )
        return manifest_path

    binary_installer = get_installer("binary")
    installed_binaries: dict[str, InstallDefinition] = {}
    errors: list[str] = []
    for name, install_def in sorted(binary_packages.items()):
        try:
            binary_installer.install_packages(
                project_root,
                {name: install_def},
                force=force,
            )
            installed_binaries[name] = install_def
        except InstallError as exc:
            errors.append(f"{name}: {exc.message}")

    if installed_binaries:
        write_manifest(
            project_root,
            python_packages={},
            binary_packages=installed_binaries,
        )

    write_install_lockfile(
        project_root,
        python_packages=python_packages,
        binary_packages=installed_binaries,
    )

    if errors:
        summary = "; ".join(errors)
        raise InstallError(
            f"binary install failed for {len(errors)} tool(s): {summary}",
            hint="python packages were installed; fix binary prerequisites and retry",
        )
    return manifest_path


def read_manifest(project_root: Path) -> dict:
    manifest_path = tools_manifest_path(project_root)
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data
