"""Shared fixtures for refactor runner/CLI tests."""

from __future__ import annotations

from refactor.protocol import ApplyMode
from refactor.registry import RULES

NON_AUTO_RULE_IDS = frozenset(
    rule.rule_id for rule in RULES if rule.apply_mode is not ApplyMode.AUTO
)

BEFORE = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d[key] if key in d else 0
    return value
"""

AFTER = """\
def pick(d: dict[str, int], key: str) -> int:
    value = d.get(key, 0)
    return value
"""

MULTI_BEFORE = """\
def f(items=[]):
    cache = dict()
"""

MULTI_AFTER = """\
def f(items=[]):
    cache = {}
"""
