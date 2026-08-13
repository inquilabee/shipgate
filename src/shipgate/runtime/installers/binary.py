"""Binary tool installers."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Protocol

from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_BIN_DIR, contained_child
from shipgate.runtime.installers.binary_github import GitHubReleaseInstaller
from shipgate.runtime.installers.binary_npm import NpmInstaller
from shipgate.runtime.installers.binary_path import PathBinaryInstaller
from shipgate.runtime.installers.version_spec import assert_exact_pin

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition

__all__ = [
    "BinaryInstallStrategy",
    "BinaryInstaller",
    "GitHubReleaseInstaller",
    "NpmInstaller",
    "PathBinaryInstaller",
]


class BinaryInstallStrategy(Protocol):
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool: ...

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        """Install a binary tool to the destination path."""
        ...


class BinaryInstaller:
    manager = "binary"

    def __init__(self, strategies: tuple[BinaryInstallStrategy, ...] | None = None) -> None:
        self._strategies = strategies or (
            PathBinaryInstaller(),
            GitHubReleaseInstaller(),
            NpmInstaller(),
        )

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
        *,
        force: bool = False,
    ) -> None:
        bin_dir = project_root / PROJECT_MANAGED_BIN_DIR
        bin_dir.mkdir(parents=True, exist_ok=True)
        for _name, install_def in sorted(packages.items()):
            self._refuse_known_bad(install_def)
            binary_name = install_def.binary or install_def.package
            try:
                leaf = contained_child(bin_dir, binary_name)
            except ValueError as exc:
                raise InstallError(
                    f"binary {binary_name!r} escapes managed bin dir",
                ) from exc
            destination = leaf.with_suffix(".exe") if sys.platform == "win32" else leaf
            if destination.is_file() and not force:
                continue
            if destination.is_file() and force:
                destination.unlink()
            strategy = self._resolve_strategy(binary_name, install_def)
            strategy.install(bin_dir, binary_name, install_def, destination)

    def _resolve_strategy(
        self,
        binary_name: str,
        install_def: InstallDefinition,
    ) -> BinaryInstallStrategy:
        for strategy in self._strategies:
            if strategy.can_install(binary_name, install_def):
                return strategy
        raise InstallError(
            f"binary {binary_name!r} is not available on PATH and has no managed installer",
            hint="install the tool manually or add it to PATH",
        )

    @staticmethod
    def _refuse_known_bad(install_def: InstallDefinition) -> None:
        pin = assert_exact_pin(install_def.version, kind="binary").lstrip("v")
        bad = {item.strip().lstrip("v") for item in install_def.known_bad if item.strip()}
        if pin in bad:
            raise InstallError(
                f"refusing to install {install_def.package}@{install_def.version}: known_bad"
            )
