"""Python package installer."""

from __future__ import annotations

import subprocess
import sys
from typing import TYPE_CHECKING

from shipgate.errors import InstallError
from shipgate.paths import managed_python_env

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition


class PythonInstaller:
    manager = "python"

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
    ) -> None:
        venv = managed_python_env(project_root)
        if not venv.exists():
            subprocess.run(  # noqa: S603
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
                capture_output=True,
                text=True,
            )
        if sys.platform == "win32":
            pip = venv / "Scripts" / "pip"
        else:
            pip = venv / "bin" / "pip"
        for package, install_def in sorted(packages.items()):
            specs = [package]
            if install_def.version:
                specs[0] = f"{package}{install_def.version}"
            specs.extend(install_def.requires)
            for spec in specs:
                result = subprocess.run(  # noqa: S603
                    [str(pip), "install", spec],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    raise InstallError(
                        f"failed to install {spec}: {result.stderr.strip()}",
                    )
