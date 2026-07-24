"""Discover and cache the project's Python environment for import-resolution tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import ShipGateError
from shipgate.paths import (
    PROJECT_CACHE_ENV,
    PROJECT_ENV_CACHE_KEY,
    PROJECT_MANAGED_PYTHON_ENV,
    parse_env_file,
    update_project_cache_env,
)

if TYPE_CHECKING:
    from collections.abc import Mapping


class ProjectPythonResolver:
    PROJECT_VENV_NAMES = (".venv", "venv")

    @staticmethod
    def discover(
        project_root: Path,
        *,
        process_environ: Mapping[str, str] | None = None,
    ) -> Path | None:
        root = project_root.resolve()
        managed_root = (root / PROJECT_MANAGED_PYTHON_ENV).resolve()
        for name in ProjectPythonResolver.PROJECT_VENV_NAMES:
            candidate = root / name
            if ProjectPythonResolver._is_python_env(candidate):
                return ProjectPythonResolver._cache_path(root, candidate)
        virtual_env = (process_environ or os.environ).get("VIRTUAL_ENV")
        if virtual_env:
            env_path = Path(virtual_env).resolve()
            if ProjectPythonResolver._is_python_env(
                env_path
            ) and not ProjectPythonResolver._is_under(env_path, managed_root):
                return ProjectPythonResolver._cache_path(root, env_path)
        return None

    @staticmethod
    def resolve(
        project_root: Path,
        *,
        process_environ: Mapping[str, str] | None = None,
    ) -> Path | None:
        cached = ProjectPythonResolver.read_cached_project_python(project_root)
        if cached is not None:
            return cached
        discovered = ProjectPythonResolver.discover(
            project_root,
            process_environ=process_environ,
        )
        if discovered is not None:
            persist_project_python(project_root, discovered)
        return discovered

    @staticmethod
    def read_cached_project_python(project_root: Path) -> Path | None:
        env_path = project_root / PROJECT_CACHE_ENV
        if not env_path.is_file():
            return None
        raw = parse_env_file(env_path).get(PROJECT_ENV_CACHE_KEY)
        if not raw:
            return None
        return resolve_cached_project_python(project_root, raw)

    @staticmethod
    def _is_python_env(path: Path) -> bool:
        if not path.is_dir():
            return False
        if sys.platform == "win32":
            return (path / "Scripts" / "python.exe").is_file()
        return (path / "bin" / "python").is_file()

    @staticmethod
    def _is_under(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
        except ValueError:
            return False
        return True

    @staticmethod
    def _cache_path(project_root: Path, env_path: Path) -> Path:
        resolved = env_path.resolve()
        try:
            return resolved.relative_to(project_root.resolve())
        except ValueError:
            return resolved


def read_cached_project_python(project_root: Path) -> Path | None:
    return ProjectPythonResolver.read_cached_project_python(project_root)


def resolve_cached_project_python(project_root: Path, raw: str) -> Path | None:
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    resolved = candidate.resolve()
    managed_root = (project_root / PROJECT_MANAGED_PYTHON_ENV).resolve()
    if ProjectPythonResolver._is_under(resolved, managed_root):
        return None
    if not ProjectPythonResolver._is_python_env(resolved):
        return None
    return ProjectPythonResolver._cache_path(project_root, resolved)


def validate_project_python(project_root: Path, raw: Path) -> Path:
    resolved = resolve_cached_project_python(project_root, str(raw))
    if resolved is None:
        msg = f"project Python environment not found or invalid: {raw}"
        raise ShipGateError(msg)
    return resolved


def persist_project_python(project_root: Path, env_path: Path) -> Path:
    normalized = validate_project_python(project_root, env_path)
    update_project_cache_env(
        project_root,
        {PROJECT_ENV_CACHE_KEY: str(normalized).replace("\\", "/")},
    )
    return normalized


def discover_and_persist_project_python(project_root: Path) -> Path | None:
    discovered = ProjectPythonResolver.discover(project_root)
    if discovered is None:
        return None
    return persist_project_python(project_root, discovered)


def discover_project_python(
    project_root: Path,
    *,
    process_environ: Mapping[str, str] | None = None,
) -> Path | None:
    return ProjectPythonResolver.resolve(
        project_root,
        process_environ=process_environ,
    )
