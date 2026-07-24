from shipgate.catalog.loader import CatalogLoader


def test_catalog_loads_suites():
    catalog = CatalogLoader.load()
    assert "standard" in catalog.suites
    assert "ci" in catalog.suites
    assert "ruff.lint" in catalog.suites["python-quality"].members
