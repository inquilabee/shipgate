import tomllib
from pathlib import Path

from shipgate import __version__


def test_version_matches_pyproject():
    root = Path(__file__).resolve().parents[2]
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    assert __version__ == data["project"]["version"]
