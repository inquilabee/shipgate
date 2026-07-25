import pytest

from shipgate.domain.ids import validate_id


def test_accepts_ruff_lint():
    assert validate_id("ruff.lint") == "ruff.lint"


def test_accepts_python_quality():
    assert validate_id("python-quality") == "python-quality"


def test_rejects_empty():
    with pytest.raises(ValueError, match="must not be empty"):
        validate_id("")


def test_rejects_path_separator():
    with pytest.raises(ValueError, match="invalid id"):
        validate_id("../tool")


def test_rejects_uppercase():
    with pytest.raises(ValueError, match="invalid id"):
        validate_id("Ruff Lint")
