"""Plugin loader stub."""

from shipgate.normalize.base import NORMALIZERS


def load_normalizers() -> dict:
    return dict(NORMALIZERS)
