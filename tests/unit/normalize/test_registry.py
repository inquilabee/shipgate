"""Normalizer registry behavior."""

import pytest

from shipgate.normalize import get_normalizer
from shipgate.normalize.core import GenericExitNormalizer


def test_get_normalizer_known_id():
    normalizer = get_normalizer("generic_exit")
    assert isinstance(normalizer, GenericExitNormalizer)


def test_get_normalizer_unknown_id_raises():
    with pytest.raises(ValueError, match="unknown normalizer"):
        get_normalizer("not-a-real-normalizer")
