"""PATH-based binary installer strategy."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.runtime.installers.base import link_binary

if TYPE_CHECKING:
    from shipgate.domain.catalog import InstallDefinition


class PathBinaryInstaller:
    def can_install(self, binary_name: str, install_def: InstallDefinition) -> bool:  # ruff:ignore[no-self-use]
        return install_def.allow_path and shutil.which(binary_name) is not None

    def install(  # ruff:ignore[no-self-use]
        self,
        bin_dir: Path,
        binary_name: str,
        install_def: InstallDefinition,
        destination: Path,
    ) -> None:
        _ = bin_dir, install_def
        existing = shutil.which(binary_name)
        if existing is None:
            raise InstallError(f"binary {binary_name!r} is not available on PATH")
        link_binary(Path(existing), destination)
