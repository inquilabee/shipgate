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
