import pytest

from shipgate.catalog.core.validate import CatalogValidator
from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import Catalog, CliOptionDefinition, SuiteDefinition, ToolDefinition
from shipgate.domain.modes import RunMode
from shipgate.errors import CatalogError


def test_bundled_tools_declare_scope():
    catalog = CatalogLoader.load()
    for tool_id, tool in catalog.tools.items():
        assert tool.scope.delivery in {"root", "dirs", "files"}, tool_id
    CatalogValidator.validate(catalog)


def test_cycle_fails():
    catalog = Catalog(
        tools={"a.tool": ToolDefinition(id="a.tool", executable="a", modes=(RunMode.CHECK,))},
        suites={
            "s1": SuiteDefinition(id="s1", members=("s2",)),
            "s2": SuiteDefinition(id="s2", members=("s1",)),
        },
    )
    with pytest.raises(CatalogError, match="cycle"):
        CatalogValidator.validate(catalog)


def test_validator_class_entry_rejects_bad_cli_style():
    catalog = Catalog(
        tools={
            "bad.tool": ToolDefinition(
                id="bad.tool",
                executable="bad",
                modes=(RunMode.CHECK,),
                cli={"paths": CliOptionDefinition(flag="--paths", style="invalid")},
            )
        },
        suites={},
    )
    with pytest.raises(CatalogError, match="unsupported style"):
        CatalogValidator.validate(catalog)


def test_missing_member_fails():
    catalog = Catalog(
        tools={},
        suites={"bad": SuiteDefinition(id="bad", members=("missing.tool",))},
    )
    with pytest.raises(CatalogError):
        CatalogValidator.validate(catalog)
