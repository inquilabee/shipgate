"""Managed tool installation."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.paths import managed_python_env, tools_dir
from shipgate.planning.suites import expand_suite
from shipgate.runtime.environment import tools_manifest_path

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import Catalog, InstallDefinition

MANIFEST_SCHEMA = "shipgate.install.v1"


def collect_install_requirements(suite_id: str, catalog: Catalog) -> dict[str, InstallDefinition]:
    tool_ids = expand_suite(suite_id, catalog)
    packages: dict[str, InstallDefinition] = {}
    for tool_id in tool_ids:
        tool = catalog.get_tool(tool_id)
        if tool.install and tool.install.manager == "python":
            packages[tool.install.package] = tool.install
    return packages


def install_suite(project_root: Path, suite_id: str, catalog: Catalog) -> Path:
    packages = collect_install_requirements(suite_id, catalog)
    if not packages:
        return tools_manifest_path(project_root)
    venv = managed_python_env(project_root)
    tools_dir(project_root).mkdir(parents=True, exist_ok=True)
    if not venv.exists():
        subprocess.run(  # noqa: S603
            [sys.executable, "-m", "venv", str(venv)],
            check=True,
            capture_output=True,
            text=True,
        )
    if sys.platform == "win32":
        pip = venv / "Scripts" / "pip"
    else:
        pip = venv / "bin" / "pip"
    for package, install_def in sorted(packages.items()):
        spec = package
        if install_def.version:
            spec = f"{package}{install_def.version}"
        result = subprocess.run(  # noqa: S603
            [str(pip), "install", spec],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise InstallError(
                f"failed to install {package}: {result.stderr.strip()}",
            )
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "packages": {pkg: install_def.version or "latest" for pkg, install_def in packages.items()},
    }
    manifest_path = tools_manifest_path(project_root)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path
