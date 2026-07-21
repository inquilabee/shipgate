import pytest

from shipgate.domain.ids import CheckId, RunnableId, SuiteId, validate_id


def test_accepts_ruff_lint():
    assert validate_id("ruff.lint") == "ruff.lint"


def test_accepts_python_quality():
    assert SuiteId("python-quality").value == "python-quality"


def test_rejects_empty():
    with pytest.raises(ValueError):
        validate_id("")


def test_rejects_path_separator():
    with pytest.raises(ValueError):
        RunnableId("../tool")


def test_rejects_uppercase():
    with pytest.raises(ValueError):
        CheckId("Ruff Lint")
