"""Normalizer ID registry derived from normalize package."""

from __future__ import annotations

from shipgate.normalize import NORMALIZERS

VALID_NORMALIZERS = frozenset(NORMALIZERS)
