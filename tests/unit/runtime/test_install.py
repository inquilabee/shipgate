from shipgate.catalog.loader import load_catalog
from shipgate.runtime.install import collect_install_requirements


def test_install_plan_deduplicates_packages():
    catalog = load_catalog()
    python_packages, _binaries = collect_install_requirements("full", catalog)
    ruff_count = sum(1 for p in python_packages if p == "ruff")
    assert ruff_count == 1


def test_install_plan_collects_binaries():
    catalog = load_catalog()
    _python, binaries = collect_install_requirements("security", catalog)
    assert "gitleaks" in binaries
