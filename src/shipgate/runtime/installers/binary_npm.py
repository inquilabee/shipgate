"""npm-based binary installer strategy."""

from __future__ import annotations

import shutil
import sys
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.runtime.installers.base import link_binary
from shipgate.runtime.installers.version_spec import npm_package_spec

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition


class NpmInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:  # ruff:ignore[no-self-use]
        _ = binary_name
        return install_def.manager == "binary" and install_def.download is None

    def install(  # ruff:ignore[no-self-use]
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        npm = shutil.which("npm")
        if npm is None:
            raise InstallError(f"npm is required to install {install_def.package}")
        package_spec = npm_package_spec(install_def.package, install_def.version)
        result = run_command(
            [npm, "install", "--prefix", str(bin_dir), package_spec],
        )
        if result.returncode != 0:
            raise InstallError(
                f"failed to install {package_spec}: {result.stderr.strip()}",
            )
        installed = bin_dir / "node_modules" / ".bin" / binary_name
        if sys.platform == "win32":
            installed = installed.with_suffix(".cmd")
        if not installed.is_file():
            raise InstallError(f"{install_def.package} install did not produce an executable")
        link_binary(installed, destination)
