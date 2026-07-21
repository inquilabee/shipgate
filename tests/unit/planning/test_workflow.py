import pytest

from shipgate.catalog.loader import load_catalog
from shipgate.domain.modes import RunMode
from shipgate.domain.project import ProjectConfig
from shipgate.errors import PlanningError
from shipgate.planning.suites import expand_suite
from shipgate.planning.workflow import resolve_runnables


@pytest.fixture
def catalog():
    return load_catalog()


def test_default_selects_standard(catalog):
    suite_id, tools = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
    )
    assert suite_id == "standard"
    assert tools == ["ruff.lint"]


def test_suite_override(catalog):
    _, tools = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
        suite_override="python-quality",
    )
    assert tools == ["ruff.lint"]


def test_check_override(catalog):
    suite_id, tools = resolve_runnables(
        mode=RunMode.CHECK,
        project=ProjectConfig(),
        catalog=catalog,
        check_override="ruff.lint",
    )
    assert suite_id == "ruff.lint"
    assert tools == ["ruff.lint"]


def test_unknown_suite_fails(catalog):
    with pytest.raises(PlanningError):
        resolve_runnables(
            mode=RunMode.CHECK,
            project=ProjectConfig(),
            catalog=catalog,
            suite_override="nope",
        )


def test_nested_suite_expands(catalog):
    tools = expand_suite("standard", catalog)
    assert tools == ["ruff.lint"]


def test_duplicate_leaves_deduped(catalog):
    catalog_data = catalog
    tools = expand_suite("full", catalog_data)
    assert tools.count("ruff.lint") == 1
