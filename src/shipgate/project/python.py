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

    def __init__(
        self,
        project_root: Path,
        *,
        process_environ: Mapping[str, str] | None = None,
    ) -> None:
        self.root = project_root.resolve()
        self.process_environ = process_environ or os.environ
        self.managed_root = (self.root / PROJECT_MANAGED_PYTHON_ENV).resolve()

    def discover(self) -> Path | None:
        for name in self.PROJECT_VENV_NAMES:
            candidate = self.root / name
            if self.is_python_env(candidate):
                return self.cache_path(candidate)
        if virtual_env := self.process_environ.get("VIRTUAL_ENV"):
            env_path = Path(virtual_env).resolve()
            if self.is_python_env(env_path) and not self.is_under(env_path):
                return self.cache_path(env_path)
        return None

    def resolve(self) -> Path | None:
        cached = self.read_cached_project_python()
        if cached is not None:
            return cached
        discovered = self.discover()
        if discovered is not None:
            persist_project_python(self.root, discovered)
        return discovered

    def read_cached_project_python(self) -> Path | None:
        env_path = self.root / PROJECT_CACHE_ENV
        if not env_path.is_file():
            return None
        raw = parse_env_file(env_path).get(PROJECT_ENV_CACHE_KEY)
        if not raw:
            return None
        return resolve_cached_project_python(self.root, raw)

    def is_python_env(self, path: Path) -> bool:
        _ = self
        return (
            (
                (path / "Scripts" / "python.exe").is_file()
                if sys.platform == "win32"
                else (path / "bin" / "python").is_file()
            )
            if path.is_dir()
            else False
        )

    def is_under(self, path: Path) -> bool:
        try:
            path.relative_to(self.managed_root)
        except ValueError:
            return False
        return True

    def cache_path(self, env_path: Path) -> Path:
        resolved = env_path.resolve()
        try:
            return resolved.relative_to(self.root)
        except ValueError:
            return resolved


def read_cached_project_python(project_root: Path) -> Path | None:
    return ProjectPythonResolver(project_root).read_cached_project_python()


def resolve_cached_project_python(project_root: Path, raw: str) -> Path | None:
    resolver = ProjectPythonResolver(project_root)
    raw_path = Path(raw)
    candidate = raw_path if raw_path.is_absolute() else project_root / raw_path
    resolved = candidate.resolve()
    if resolver.is_under(resolved):
        return None
    if not resolver.is_python_env(resolved):
        return None
    return resolver.cache_path(resolved)


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
    discovered = ProjectPythonResolver(project_root).discover()
    return None if discovered is None else persist_project_python(project_root, discovered)


def discover_project_python(
    project_root: Path,
    *,
    process_environ: Mapping[str, str] | None = None,
) -> Path | None:
    return ProjectPythonResolver(
        project_root,
        process_environ=process_environ,
    ).resolve()
