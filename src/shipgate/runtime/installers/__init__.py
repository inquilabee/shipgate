"""Installer strategy registry."""

from __future__ import annotations

from shipgate.runtime.installers.binary import BinaryInstaller
from shipgate.runtime.installers.python import PythonInstaller
from shipgate.runtime.installers.registry import INSTALLER_REGISTRY, get_installer

__all__ = [
    "INSTALLER_REGISTRY",
    "BinaryInstaller",
    "PythonInstaller",
    "get_installer",
]
