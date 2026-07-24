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
        }
    )
    tool = catalog.get_tool("example.lint")
    assert tool.executable == "example"
    assert tool.modes == (RunMode.CHECK,)
    assert tool.scope.extensions == (".py",)
    assert catalog.suites["standard"].members == ("example.lint",)


def demo_tool_raw() -> dict:
    return {
        "executable": "demo",
        "modes": ["check"],
        "tags": ["security"],
        "cache": {"results": True, "ttl_seconds": 60},
        "suggest_if": {"files_present": ["**/Dockerfile"]},
        "install": {
            "manager": "binary",
            "package": "demo",
            "version": "1.2.3",
            "binary": "demo",
            "known_bad": ["1.0.0"],
            "download": {
                "repo": "org/demo",
                "asset_template": "demo_{version}_{os}_{arch}",
                "binary_name": "demo",
                "arch_map": {"x86_64": "amd64"},
            },
        },
        "scope": {"extensions": ["py"]},
    }


def test_parse_tool_tags_cache_suggest():
    catalog = CatalogParser.parse({"tools": {"demo.tool": demo_tool_raw()}, "suites": {}})
    tool = catalog.get_tool("demo.tool")
    assert tool.tags == ("security",)
    assert tool.cache is not None
    assert tool.cache.ttl_seconds == 60
    assert tool.suggest_if is not None
    assert tool.suggest_if.files_present == ("**/Dockerfile",)


def test_parse_install_download_and_known_bad():
    catalog = CatalogParser.parse({"tools": {"demo.tool": demo_tool_raw()}, "suites": {}})
    tool = catalog.get_tool("demo.tool")
    assert tool.install is not None
    assert tool.install.version == "1.2.3"
    assert tool.install.known_bad == ("1.0.0",)
    assert tool.install.download is not None
    assert tool.install.download.repo == "org/demo"
    assert tool.install.download.arch_map["x86_64"] == "amd64"
