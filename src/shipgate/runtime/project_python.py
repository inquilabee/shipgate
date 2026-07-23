"""Discover the project's Python environment for import-resolution tools."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.paths import managed_python_env

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
        managed_root = managed_python_env(root).resolve()
        for name in ProjectPythonResolver.PROJECT_VENV_NAMES:
            candidate = root / name
            if ProjectPythonResolver._is_python_env(candidate):
                return Path(name)
        virtual_env = (process_environ or os.environ).get("VIRTUAL_ENV")
        if virtual_env:
            env_path = Path(virtual_env).resolve()
            if ProjectPythonResolver._is_python_env(
                env_path
            ) and not ProjectPythonResolver._is_under(env_path, managed_root):
                return env_path
        return None

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


def discover_project_python(
    project_root: Path,
    *,
    process_environ: Mapping[str, str] | None = None,
) -> Path | None:
    return ProjectPythonResolver.discover(
        project_root,
        process_environ=process_environ,
    )
