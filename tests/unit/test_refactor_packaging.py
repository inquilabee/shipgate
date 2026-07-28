"""Regression tests for refactor packaging in the ShipGate wheel."""

from __future__ import annotations

import shutil
import tomllib
import zipfile
from importlib import import_module
from pathlib import Path
from subprocess import run

from refactor.inventory import DEFAULT_INVENTORY_PATH, load_inventory

REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_IN_WHEEL = "refactor/inventory/rule_ids.yaml"
SHIPGATE_SCRIPT = "shipgate.cli:main"
REFACTOR_MODULE_MAIN = "refactor.cli:main"


def test_inventory_package_data_is_loadable() -> None:
    assert DEFAULT_INVENTORY_PATH.is_file()
    assert len(load_inventory()) >= 150


def test_no_standalone_refactor_console_script() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject["project"]["scripts"]
    assert "refactor" not in scripts
    assert scripts["shipgate"] == SHIPGATE_SCRIPT
    module_name, attr = REFACTOR_MODULE_MAIN.split(":")
    target = getattr(import_module(module_name), attr)
    assert callable(target)


def test_wheel_includes_refactor_inventory(tmp_path: Path) -> None:
    uv = shutil.which("uv")
    assert uv is not None, "uv must be on PATH for wheel packaging test"
    dist = tmp_path / "dist"
    run([uv, "build", "-o", str(dist)], check=True, cwd=REPO_ROOT)
    wheel = next(dist.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
    assert INVENTORY_IN_WHEEL in names
    assert any(name.endswith("refactor/cli.py") for name in names)
