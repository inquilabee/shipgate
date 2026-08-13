"""Python package installer."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from shipgate.core.process import run_command
from shipgate.errors import InstallError
from shipgate.paths import PROJECT_MANAGED_PYTHON_ENV
from shipgate.runtime.installers.version_spec import pip_package_spec

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition


class PythonInstaller:
    manager = "python"

    def install_packages(
        self,
        project_root: Path,
        packages: dict[str, InstallDefinition],
        *,
        force: bool = False,
    ) -> None:
        del force  # pip install always refreshes to the requested pin
        venv = project_root / PROJECT_MANAGED_PYTHON_ENV
        if not venv.exists():
            run_command(
                [sys.executable, "-m", "venv", str(venv)],
                check=True,
            )
        pip = venv / "Scripts" / "pip" if sys.platform == "win32" else venv / "bin" / "pip"
        for package, install_def in sorted(packages.items()):
            self._refuse_known_bad(install_def)
            name = install_def.package or package
            specs = [pip_package_spec(name, install_def.version)]
            specs.extend(install_def.requires)
            for spec in specs:
                if spec.startswith("-"):
                    raise InstallError(f"refusing pip option as package spec: {spec!r}")
                result = run_command([str(pip), "install", "--", spec])
                if result.returncode != 0:
                    raise InstallError(
                        f"failed to install {spec}: {result.stderr.strip()}",
                    )

    @staticmethod
    def _refuse_known_bad(install_def: InstallDefinition) -> None:
        from shipgate.runtime.installers.version_spec import assert_exact_pin

        pin = assert_exact_pin(install_def.version, kind="python").lstrip("v")
        bad = {item.strip().lstrip("v") for item in install_def.known_bad if item.strip()}
        if pin in bad:
            raise InstallError(
                f"refusing to install {install_def.package}@{install_def.version}: known_bad"
            )
