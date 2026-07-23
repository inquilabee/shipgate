"""Regression tests for bundled catalog files shipped in the wheel."""

from __future__ import annotations

import shutil
import zipfile
from importlib import resources
from pathlib import Path
from subprocess import run

SETUP_GITIGNORE = "shipgate/catalog/bundled/setup/.gitignore"


def test_bundled_setup_gitignore_is_accessible() -> None:
    path = resources.files("shipgate.catalog.bundled") / "setup" / ".gitignore"
    assert path.is_file(), "bundled setup .gitignore must be present in package data"


def test_wheel_includes_bundled_setup_gitignore(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "uv must be on PATH for wheel packaging test"
    dist = tmp_path / "dist"
    run([uv, "build", "-o", str(dist)], check=True, cwd=Path(__file__).resolve().parents[3])
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert SETUP_GITIGNORE in names
