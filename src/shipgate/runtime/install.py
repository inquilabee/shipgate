"""Managed tool installation."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from shipgate.catalog.core.python_spec import PythonVersionSpec, host_python_minor
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_TOOLS_DIR
from shipgate.planning.core.suites import expand_suite
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.installers.registry import get_installer
from shipgate.runtime.lockfile import write_lockfile
from shipgate.runtime.tool_manifest import ManagedToolState, read_manifest, write_manifest

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, InstallDefinition

__all__ = [
    "ManagedToolState",
    "collect_install_requirements",
    "collect_install_requirements_for_tools",
    "install_binaries",
    "install_suite",
    "partition_python_packages",
    "read_manifest",
    "write_install_lockfile",
    "write_manifest",
]


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
        match tool.install.manager:
            case "python":
                python_packages[tool.install.package] = tool.install
            case "binary":
                key = tool.install.binary or tool.install.package
                binary_packages[key] = tool.install
    return python_packages, binary_packages


def partition_python_packages(
    packages: dict[str, InstallDefinition],
) -> tuple[dict[str, InstallDefinition], tuple[str, ...]]:
    version = host_python_minor()
    kept: dict[str, InstallDefinition] = {}
    skipped: list[str] = []
    for name, install_def in packages.items():
        if not install_def.requires_python:
            kept[name] = install_def
            continue
        message = PythonVersionSpec.parse(install_def.requires_python).unsupported_message(
            name,
            version,
        )
        if message is None:
            kept[name] = install_def
        else:
            skipped.append(message)
    return kept, tuple(skipped)


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
    python_packages, skipped = partition_python_packages(python_packages)
    for reason in skipped:
        sys.stderr.write(f"{reason}\n")
    if not force and ManagedToolState(project_root).satisfies(python_packages, binary_packages):
        sys.stderr.write("shipgate install: managed tools already satisfied\n")
        return tools_manifest_path(project_root)
    (project_root / PROJECT_TOOLS_DIR).mkdir(parents=True, exist_ok=True)
    if python_packages:
        get_installer("python").install_packages(project_root, python_packages, force=force)
    manifest_path = write_manifest(
        project_root,
        python_packages=python_packages,
        binary_packages={},
    )
    installed_binaries, errors = install_binaries(project_root, binary_packages, force=force)
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


def install_binaries(
    project_root: Path,
    binary_packages: dict[str, InstallDefinition],
    *,
    force: bool,
) -> tuple[dict[str, InstallDefinition], list[str]]:
    """Install each managed binary independently; collect per-tool errors."""
    if not binary_packages:
        return {}, []
    binary_installer = get_installer("binary")
    installed: dict[str, InstallDefinition] = {}
    errors: list[str] = []
    for name, install_def in sorted(binary_packages.items()):
        try:
            binary_installer.install_packages(project_root, {name: install_def}, force=force)
            installed[name] = install_def
        except InstallError as exc:
            errors.append(f"{name}: {exc.message}")
    return installed, errors
