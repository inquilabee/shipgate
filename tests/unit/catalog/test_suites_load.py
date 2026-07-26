from shipgate.catalog.loader import CatalogLoader


def test_catalog_loads_suites():
    catalog = CatalogLoader.load()
    assert "standard" in catalog.suites
    assert "ci" in catalog.suites
    assert "ruff.lint" in catalog.suites["python-quality"].members
    assert "pip-audit.audit" in catalog.suites["security"].members
    assert "deptry.check" in catalog.suites["extended"].members
    assert "import-linter.check" in catalog.suites["policy"].members


def test_new_tool_normalizers_and_install():
    catalog = CatalogLoader.load()
    pip_audit = catalog.get_tool("pip-audit.audit")
    deptry = catalog.get_tool("deptry.check")
    import_linter = catalog.get_tool("import-linter.check")
    assert pip_audit.normalizer == "pip_audit"
    assert deptry.normalizer == "deptry"
    assert import_linter.normalizer == "generic_exit"
    assert pip_audit.install is not None
    assert pip_audit.install.package == "pip-audit"
    assert deptry.install is not None
    assert deptry.install.package == "deptry"
    assert import_linter.install is not None
    assert import_linter.install.package == "import-linter"


def test_import_linter_and_deptry_config_wiring():
    catalog = CatalogLoader.load()
    deptry = catalog.get_tool("deptry.check")
    import_linter = catalog.get_tool("import-linter.check")
    assert import_linter.configuration.bundled == "configs/importlinter.ini"
    assert deptry.configuration.bundled is None
    assert "config" not in deptry.cli
