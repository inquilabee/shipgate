"""Managed-tool manifest: persistence and desired-state comparison."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from shipgate.paths import PROJECT_MANAGED_BIN_DIR, PROJECT_MANAGED_PYTHON_ENV
from shipgate.runtime.environment import find_in_bin_dir, tools_manifest_path

if TYPE_CHECKING:
    from pathlib import Path

    from shipgate.domain.catalog import InstallDefinition

MANIFEST_SCHEMA = "shipgate.install.v1"


def read_manifest(project_root: Path) -> dict:
    manifest_path = tools_manifest_path(project_root)
    if not manifest_path.is_file():
        return {}
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def write_manifest(
    project_root: Path,
    *,
    python_packages: dict[str, InstallDefinition],
    binary_packages: dict[str, InstallDefinition],
) -> Path:
    manifest = read_manifest(project_root)
    manifest |= {
        "schema_version": MANIFEST_SCHEMA,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "packages": {
            **manifest.get("packages", {}),
            **{
                pkg: install_def.version or "latest" for pkg, install_def in python_packages.items()
            },
        },
        "binaries": {
            **manifest.get("binaries", {}),
            **{
                name: install_def.version or "latest"
                for name, install_def in binary_packages.items()
            },
        },
    }
    manifest_path = tools_manifest_path(project_root)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


class ManagedToolState:
    """The managed tool set recorded for a project, matched against a desired set.

    Backs the `shipgate install` short-circuit: a satisfied state means every
    desired tool is already recorded at its pin and present on disk, so the
    installers can be skipped. Stale extra manifest entries (a tool dropped from
    the suite) do not make the state unsatisfied.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._manifest = read_manifest(project_root)

    def satisfies(
        self,
        python_packages: dict[str, InstallDefinition],
        binary_packages: dict[str, InstallDefinition],
    ) -> bool:
        return (
            self._venv_present()
            and self._python_matches()
            and self._packages_recorded(python_packages)
            and self._binaries_present(binary_packages)
        )

    def _venv_present(self) -> bool:
        return (self._root / PROJECT_MANAGED_PYTHON_ENV).exists()

    def _python_matches(self) -> bool:
        stored = str(self._manifest.get("python", ""))
        want = f"{sys.version_info.major}.{sys.version_info.minor}"
        return stored == want or stored.startswith(f"{want}.")

    def _packages_recorded(self, desired: dict[str, InstallDefinition]) -> bool:
        recorded = self._manifest.get("packages", {})
        return all(
            recorded.get(name) == (install_def.version or "latest")
            for name, install_def in desired.items()
        )

    def _binaries_present(self, desired: dict[str, InstallDefinition]) -> bool:
        recorded = self._manifest.get("binaries", {})
        bin_dir = self._root / PROJECT_MANAGED_BIN_DIR
        return all(
            recorded.get(key) == (install_def.version or "latest")
            and find_in_bin_dir(bin_dir, install_def.binary or install_def.package) is not None
            for key, install_def in desired.items()
        )
