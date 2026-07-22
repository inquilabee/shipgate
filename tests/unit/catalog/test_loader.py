from importlib import resources
from pathlib import Path

from shipgate.catalog.loader import load_catalog


def test_valid_catalog_loads():
    catalog = load_catalog()
    assert "ruff.lint" in catalog.tools
    assert "standard" in catalog.suites


def test_suite_members_exist():
    catalog = load_catalog()
    for suite in catalog.suites.values():
        for member in suite.members:
            assert member in catalog.tools or member in catalog.suites


def test_tool_file_stem_matches_tool_id():
    bundled = resources.files("shipgate.catalog.bundled")
    tools_dir = Path(str(bundled / "catalog" / "tools"))
    for tool_path in sorted(tools_dir.glob("*.yaml")):
        catalog = load_catalog()
        assert tool_path.stem in catalog.tools
