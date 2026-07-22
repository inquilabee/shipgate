"""Installer factory registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shipgate.runtime.installers.binary import BinaryInstaller
from shipgate.runtime.installers.python import PythonInstaller

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition
    from shipgate.runtime.installers.base import Installer

INSTALLER_REGISTRY: dict[str, Installer] = {
    "python": PythonInstaller(),
    "binary": BinaryInstaller(),
}


def get_installer(manager: str) -> Installer:
    try:
        return INSTALLER_REGISTRY[manager]
    except KeyError as exc:
        msg = f"unsupported install manager: {manager!r}"
        raise ValueError(msg) from exc


def install_by_manager(
    manager: str,
    project_root: Path,
    packages: dict[str, InstallDefinition],
) -> None:
    get_installer(manager).install_packages(project_root, packages)
