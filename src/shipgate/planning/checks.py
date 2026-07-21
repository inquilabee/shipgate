"""Check helpers."""

from shipgate.domain.catalog import Catalog


def list_checks(catalog: Catalog) -> list[str]:
    return sorted(catalog.tools.keys())
