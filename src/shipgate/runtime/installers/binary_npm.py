"""npm-based binary installer strategy."""

from __future__ import annotations

import shutil
import sys
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.runtime.installers.base import link_binary
from shipgate.runtime.installers.binary_releases import BINARY_RELEASES

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition


class NpmInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:
        return install_def.manager == "binary" and binary_name not in BINARY_RELEASES

    def install(
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        npm = shutil.which("npm")
        if npm is None:
            raise InstallError(f"npm is required to install {install_def.package}")
        result = run_command(
            [npm, "install", "--prefix", str(bin_dir), install_def.package],
        )
        if result.returncode != 0:
            raise InstallError(
                f"failed to install {install_def.package}: {result.stderr.strip()}",
            )
        installed = bin_dir / "node_modules" / ".bin" / binary_name
        if sys.platform == "win32":
            installed = installed.with_suffix(".cmd")
        if not installed.is_file():
            raise InstallError(f"{install_def.package} install did not produce an executable")
        link_binary(installed, destination)
