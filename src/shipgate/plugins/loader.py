"""Plugin loader stub."""

from shipgate.normalize import NORMALIZERS


def load_normalizers() -> dict:
    return dict(NORMALIZERS)
