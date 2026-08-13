"""Execution environment resolution."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from shipgate.domain.execution import ExecutionEnvironment
from shipgate.errors import InstallError
from shipgate.paths import (
    PROJECT_MANAGED_BIN_DIR,
    PROJECT_MANAGED_PYTHON_ENV,
    PROJECT_TOOLS_DIR,
)

if TYPE_CHECKING:
    from pathlib import Path

SECRET_SUFFIXES = ("_TOKEN", "_SECRET", "_PASSWORD", "_PASSWD", "_API_KEY")
SECRET_EXACT = frozenset(
    {
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "GITHUB_TOKEN",
        "GH_TOKEN",
        "OPENAI_API_KEY",
    }
)


def filter_environ(env: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in env.items():
        upper = key.upper()
        if upper in SECRET_EXACT:
            continue
        if any(upper.endswith(suffix) for suffix in SECRET_SUFFIXES):
            continue
        out[key] = value
    return out


def system_environment() -> ExecutionEnvironment:
    return ExecutionEnvironment(
        kind="system",
        root=None,
        env=filter_environ(dict(os.environ)),
    )


def managed_environment(project_root: Path) -> ExecutionEnvironment:
    venv = project_root / PROJECT_MANAGED_PYTHON_ENV
    bin_dir = project_root / PROJECT_MANAGED_BIN_DIR
    scripts = venv / "Scripts" if sys.platform == "win32" else venv / "bin"
    env = filter_environ(dict(os.environ))
    env.pop("VIRTUAL_ENV", None)
    path_parts: list[str] = []
    if bin_dir.is_dir():
        path_parts.append(str(bin_dir))
    if scripts.is_dir():
        path_parts.append(str(scripts))
    if path_parts:
        env["PATH"] = f"{os.pathsep.join(path_parts)}{os.pathsep}{env.get('PATH', '')}"
    apply_src_layout_pythonpath(env, project_root)
    return ExecutionEnvironment(kind="managed", root=venv, env=env)


def apply_src_layout_pythonpath(env: dict[str, str], project_root: Path) -> None:
    """Prepend src/ onto PYTHONPATH when an importable src-layout package exists."""
    from shipgate.project.layout.packages import has_src_layout_package

    if not has_src_layout_package(project_root):
        return
    src = str((project_root / "src").resolve())
    parts = [part for part in env.get("PYTHONPATH", "").split(os.pathsep) if part]
    if src not in parts:
        parts.insert(0, src)
    env["PYTHONPATH"] = os.pathsep.join(parts)


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

    if found := which(name):
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
    return str(candidate) if candidate.is_file() else None


def tools_manifest_path(project_root: Path) -> Path:
    return project_root / PROJECT_TOOLS_DIR / "manifest.json"
