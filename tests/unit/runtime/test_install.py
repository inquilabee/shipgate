from shipgate.catalog.loader import load_catalog
from shipgate.runtime.install import collect_install_requirements


def test_install_plan_deduplicates_packages():
    catalog = load_catalog()
    packages = collect_install_requirements("full", catalog)
    ruff_count = sum(1 for p in packages if p == "ruff")
    assert ruff_count == 1
