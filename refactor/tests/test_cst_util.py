from __future__ import annotations

from typing import TYPE_CHECKING

import libcst as cst
import pytest

from refactor.cst_util import HitCollector, detect_with_visitor, parse_module_cached

if TYPE_CHECKING:
    from collections.abc import Callable


class EmptyFinder(HitCollector):
    pass


def test_detect_with_visitor_reuses_cached_parse(monkeypatch: pytest.MonkeyPatch) -> None:
    parse_module_cached.cache_clear()
    calls = 0
    original_parse: Callable[[str], cst.Module] = cst.parse_module

    def counting_parse(source: str) -> cst.Module:
        nonlocal calls
        calls += 1
        return original_parse(source)

    monkeypatch.setattr(cst, "parse_module", counting_parse)
    try:
        detect_with_visitor("value = 1\n", "one.py", EmptyFinder)
        detect_with_visitor("value = 1\n", "two.py", EmptyFinder)
    finally:
        parse_module_cached.cache_clear()

    assert calls == 1
