"""Execution environment resolution."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from shipgate.domain.execution import ExecutionEnvironment
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_BIN_DIR, PROJECT_MANAGED_PYTHON_ENV, PROJECT_TOOLS_DIR

if TYPE_CHECKING:
    from pathlib import Path


def system_environment() -> ExecutionEnvironment:
    return ExecutionEnvironment(kind="system", root=None, env=dict(os.environ))


def managed_environment(project_root: Path) -> ExecutionEnvironment:
    venv = project_root / PROJECT_MANAGED_PYTHON_ENV
    bin_dir = project_root / PROJECT_MANAGED_BIN_DIR
    if sys.platform == "win32":
        scripts = venv / "Scripts"
    else:
        scripts = venv / "bin"
    env = dict(os.environ)
    env.pop("VIRTUAL_ENV", None)
    path_parts: list[str] = []
    if bin_dir.is_dir():
        path_parts.append(str(bin_dir))
    if scripts.is_dir():
        path_parts.append(str(scripts))
    if path_parts:
        env["PATH"] = f"{os.pathsep.join(path_parts)}{os.pathsep}{env.get('PATH', '')}"
    return ExecutionEnvironment(kind="managed", root=venv, env=env)


def resolve_environment(project_root: Path, env_kind: str) -> ExecutionEnvironment:
    if env_kind == "system":
        return system_environment()
    if env_kind == "managed":
        return managed_environment(project_root)
    raise InstallError(f"unknown environment kind: {env_kind!r}")


def resolve_executable(
    tool_executable: str,
    environment: ExecutionEnvironment,
    *,
    install_binary: str | None = None,
    project_root: Path | None = None,
) -> str:
    name = install_binary or tool_executable
    if project_root is not None:
        found = find_in_bin_dir(project_root / PROJECT_MANAGED_BIN_DIR, name)
        if found is not None:
            return found
    if environment.kind == "managed" and environment.root is not None:
        scripts = environment.root / ("Scripts" if sys.platform == "win32" else "bin")
        found = find_in_bin_dir(scripts, name)
        if found is not None:
            return found
    from shutil import which

    found = which(name)
    if found:
        return found
    raise InstallError(
        f"executable not found: {name}",
        hint='run "shipgate install" to install required tools',
    )


def find_in_bin_dir(bin_dir: Path, name: str) -> str | None:
    if not bin_dir.is_dir():
        return None
    if sys.platform == "win32":
        candidate = bin_dir / f"{name}.exe"
        if candidate.is_file():
            return str(candidate)
    candidate = bin_dir / name
    if candidate.is_file():
        return str(candidate)
    return None


def tools_manifest_path(project_root: Path) -> Path:
    return project_root / PROJECT_TOOLS_DIR / "manifest.json"
