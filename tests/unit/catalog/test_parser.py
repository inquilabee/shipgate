from shipgate.catalog.core import CatalogParser
from shipgate.domain.modes import RunMode


def test_parse_minimal_catalog():
    catalog = CatalogParser.parse(
        {
            "tools": {
                "example.lint": {
                    "executable": "example",
                    "modes": ["check"],
                    "scope": {"extensions": ["py"]},
                }
            },
            "suites": {"standard": {"members": ["example.lint"]}},
            "workflows": {"ci": [{"check": ["standard"]}]},
            "capabilities": {"lint": ["example.lint"]},
        }
    )
    tool = catalog.get_tool("example.lint")
    assert tool.executable == "example"
    assert tool.modes == (RunMode.CHECK,)
    assert tool.scope.extensions == (".py",)
    assert catalog.suites["standard"].members == ("example.lint",)
    assert catalog.workflows["ci"].steps[0].mode == RunMode.CHECK
    assert catalog.capabilities["lint"] == ("example.lint",)
