"""Python package installer."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_PYTHON_ENV

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
        venv = project_root / PROJECT_MANAGED_PYTHON_ENV
        if not venv.exists():
            run_command(
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
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
                result = run_command([str(pip), "install", spec])
                if result.returncode != 0:
                    raise InstallError(
                        f"failed to install {spec}: {result.stderr.strip()}",
                    )
