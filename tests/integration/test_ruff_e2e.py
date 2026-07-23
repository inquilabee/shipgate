from pathlib import Path

import pytest

from shipgate.catalog.loader import CatalogLoader
from shipgate.runtime.install import collect_install_requirements

pytestmark = pytest.mark.integration


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def catalog():
    return CatalogLoader.load()


def test_collect_install_requirements(catalog):
    python_packages, _binaries = collect_install_requirements("python-quality", catalog)
    assert "ruff" in python_packages


@pytest.mark.skipif(
    __import__("shutil").which("ruff") is None,
    reason="ruff not installed",
)
def test_ruff_clean_fixture(catalog, tmp_path):
    from shipgate.app import RunCommand, ShipGateApp

    target = FIXTURES / "python_clean"
    app = ShipGateApp(catalog=catalog)
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=target,
            quiet=True,
        )
    )
    assert code == 0


@pytest.mark.skipif(
    __import__("shutil").which("ruff") is None,
    reason="ruff not installed",
)
def test_ruff_failure_fixture(catalog, tmp_path, capsys):
    from shipgate.app import RunCommand, ShipGateApp

    target = tmp_path / "bad.py"
    target.write_text("import os\n", encoding="utf-8")
    app = ShipGateApp(catalog=catalog)
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="ruff.lint",
            target=target,
            error_format="compact",
        )
    )
    captured = capsys.readouterr()
    assert code == 1
    assert "F401" in captured.err
