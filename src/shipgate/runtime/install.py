"""Managed tool installation."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from shipgate.paths import tools_dir
from shipgate.planning.suites import expand_suite
from shipgate.runtime.environment import tools_manifest_path
from shipgate.runtime.installers.registry import get_installer

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, InstallDefinition

MANIFEST_SCHEMA = "shipgate.install.v1"


def collect_install_requirements(
    suite_id: str,
    catalog: Catalog,
) -> tuple[dict[str, InstallDefinition], dict[str, InstallDefinition]]:
    tool_ids = expand_suite(suite_id, catalog)
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


def install_suite(project_root: Path, suite_id: str, catalog: Catalog) -> Path:
    python_packages, binary_packages = collect_install_requirements(suite_id, catalog)
    tools_dir(project_root).mkdir(parents=True, exist_ok=True)
    if python_packages:
        get_installer("python").install_packages(project_root, python_packages)
    if binary_packages:
        get_installer("binary").install_packages(project_root, binary_packages)
    manifest = _read_manifest(project_root)
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


def _read_manifest(project_root: Path) -> dict:
    manifest_path = tools_manifest_path(project_root)
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    return data
