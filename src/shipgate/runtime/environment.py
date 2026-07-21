"""Execution environment resolution."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from shipgate.domain.execution import ExecutionEnvironment
from shipgate.errors import InstallError
from shipgate.paths import managed_python_env, tools_dir


def system_environment() -> ExecutionEnvironment:
    return ExecutionEnvironment(kind="system", root=None, env=dict(os.environ))


def managed_environment(project_root: Path) -> ExecutionEnvironment:
    venv = managed_python_env(project_root)
    if sys.platform == "win32":
        scripts = venv / "Scripts"
    else:
        scripts = venv / "bin"
    env = dict(os.environ)
    if scripts.is_dir():
        env["PATH"] = f"{scripts}{os.pathsep}{env.get('PATH', '')}"
        env["VIRTUAL_ENV"] = str(venv)
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
) -> str:
    name = install_binary or tool_executable
    if environment.kind == "managed" and environment.root is not None:
        if sys.platform == "win32":
            candidate = environment.root / "Scripts" / f"{name}.exe"
            if candidate.is_file():
                return str(candidate)
            candidate = environment.root / "Scripts" / name
        else:
            candidate = environment.root / "bin" / name
        if candidate.is_file():
            return str(candidate)
    from shutil import which

    found = which(name)
    if found:
        return found
    raise InstallError(
        f"executable not found: {name}",
        hint='run "shipgate install" to install required tools',
    )


def tools_manifest_path(project_root: Path) -> Path:
    return tools_dir(project_root) / "manifest.json"
