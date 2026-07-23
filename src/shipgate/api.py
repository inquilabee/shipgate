"""Public Python API."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from shipgate.app import InstallCommand, RunCommand, ShipGateApp
from shipgate.catalog.loader import CatalogLoader

if TYPE_CHECKING:
    from shipgate.domain.catalog import Catalog


def load_catalog(path: Path | None = None, *, project_root: Path | None = None) -> Catalog:
    return CatalogLoader.load(path, project_root=project_root)


def install(
    *,
    project_root: Path | None = None,
    suite: str | None = None,
    config_path: Path | None = None,
) -> int:
    root = project_root or Path.cwd()
    app = ShipGateApp()
    return app.install(InstallCommand(project_root=root, suite=suite, config_path=config_path))


def run(
    *,
    mode: str = "check",
    project_root: Path | None = None,
    suite: str | None = None,
    check: str | None = None,
    target: Path | None = None,
    config_path: Path | None = None,
    verbose: bool = False,
    quiet: bool = False,
) -> int:
    root = project_root or Path.cwd()
    app = ShipGateApp()
    cmd = RunCommand(
        project_root=root,
        config_path=config_path,
        suite=suite,
        check=check,
        target=target,
        verbose=verbose,
        quiet=quiet,
    )
    if mode == "apply" or mode == "format":
        return app.format(cmd)
    return app.check(cmd)
