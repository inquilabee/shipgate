"""Plugin registry stub."""

from shipgate.plugins.loader import load_normalizers

REGISTRY: dict = {}


def get_registry() -> dict:
    if not REGISTRY:
        REGISTRY.update(load_normalizers())
    return REGISTRY
