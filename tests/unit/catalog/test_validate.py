import pytest

from shipgate.catalog.core import CatalogValidator
from shipgate.catalog.loader import CatalogLoader
from shipgate.domain.catalog import (
    Catalog,
    CliOptionDefinition,
    InstallDefinition,
    SuiteDefinition,
    ToolDefinition,
)
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


def test_validator_rejects_range_pin():
    catalog = Catalog(
        tools={
            "bad.tool": ToolDefinition(
                id="bad.tool",
                executable="bad",
                modes=(RunMode.CHECK,),
                install=InstallDefinition(manager="python", package="bad", version=">=1.0"),
            )
        },
        suites={},
    )
    with pytest.raises(CatalogError, match="exact pin"):
        CatalogValidator.validate(catalog)


def test_validator_rejects_known_bad_pin():
    catalog = Catalog(
        tools={
            "bad.tool": ToolDefinition(
                id="bad.tool",
                executable="bad",
                modes=(RunMode.CHECK,),
                install=InstallDefinition(
                    manager="python",
                    package="bad",
                    version="1.2.3",
                    known_bad=("1.2.3",),
                ),
            )
        },
        suites={},
    )
    with pytest.raises(CatalogError, match="known_bad"):
        CatalogValidator.validate(catalog)


def test_validator_rejects_invalid_requires_python():
    catalog = Catalog(
        tools={
            "bad.tool": ToolDefinition(
                id="bad.tool",
                executable="bad",
                modes=(RunMode.CHECK,),
                install=InstallDefinition(
                    manager="python",
                    package="bad",
                    version="1.2.3",
                    requires_python="3.14",
                ),
            )
        },
        suites={},
    )
    with pytest.raises(CatalogError, match="requires_python"):
        CatalogValidator.validate(catalog)


def test_bundled_deadcode_and_semgrep_declare_requires_python():
    catalog = CatalogLoader.load()
    deadcode = catalog.get_tool("deadcode.check")
    semgrep = catalog.get_tool("semgrep.scan")
    assert deadcode.install is not None
    assert semgrep.install is not None
    assert deadcode.install.requires_python == ">=3.11,<3.14"
    assert semgrep.install.requires_python == ">=3.11,<3.14"


def test_security_tools_are_tagged():
    catalog = CatalogLoader.load()
    for tool_id in ("bandit.scan", "gitleaks.scan", "semgrep.scan"):
        assert "security" in catalog.get_tool(tool_id).tags
