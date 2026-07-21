from shipgate.catalog.loader import load_catalog


def test_catalog_loads_workflows_and_capabilities():
    catalog = load_catalog()
    assert "default" in catalog.workflows
    assert "ci" in catalog.workflows
    assert catalog.workflows["default"].steps[0].mode.value == "check"
    assert "Linting" in catalog.capabilities
    assert "ruff.lint" in catalog.capabilities["Linting"]
