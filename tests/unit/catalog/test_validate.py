import pytest
from shipgate.catalog.validate import validate_catalog
from shipgate.domain.catalog import Catalog, SuiteDefinition, ToolDefinition
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError


def test_cycle_fails():
    catalog = Catalog(
        tools={"a.tool": ToolDefinition(id="a.tool", executable="a", modes=(RunMode.CHECK,))},
        suites={
            "s1": SuiteDefinition(id="s1", members=("s2",)),
            "s2": SuiteDefinition(id="s2", members=("s1",)),
        },
    )
    with pytest.raises(CatalogError, match="cycle"):
        validate_catalog(catalog)


def test_missing_member_fails():
    catalog = Catalog(
        tools={},
        suites={"bad": SuiteDefinition(id="bad", members=("missing.tool",))},
    )
    with pytest.raises(CatalogError):
        validate_catalog(catalog)
