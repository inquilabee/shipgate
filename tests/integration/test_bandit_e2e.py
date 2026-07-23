from pathlib import Path

import pytest

from shipgate.app import RunCommand, ShipGateApp
from shipgate.catalog.loader import CatalogLoader

pytestmark = pytest.mark.integration

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


@pytest.fixture
def catalog():
    return CatalogLoader.load()


@pytest.mark.skipif(
    __import__("shutil").which("bandit") is None,
    reason="bandit not installed",
)
def test_bandit_clean_fixture(catalog, tmp_path):
    target = FIXTURES / "python_clean"
    app = ShipGateApp(catalog=catalog)
    code = app.check(
        RunCommand(
            project_root=tmp_path,
            check="bandit.scan",
            target=target,
            quiet=True,
        )
    )
    assert code == 0
