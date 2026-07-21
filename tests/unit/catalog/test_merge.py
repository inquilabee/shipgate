from pathlib import Path

from shipgate.catalog.loader import load_catalog
from shipgate.catalog.merge import load_catalog_pack, merge_catalogs


def test_merge_org_pack():
    base = load_catalog()
    pack_path = Path(__file__).resolve().parents[2] / "fixtures" / "catalogs" / "org-pack.yaml"
    pack = load_catalog_pack(pack_path)
    merged = merge_catalogs(base, pack)
    assert "org.lint" in merged.tools
    assert "org-standard" in merged.suites
