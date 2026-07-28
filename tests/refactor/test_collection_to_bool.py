"""Regression: collection-to-bool must not rewrite count-valued len()."""

from __future__ import annotations

from refactor.registry import RULES


def collection_to_bool_rule():
    return next(rule for rule in RULES if rule.rule_id == "collection-to-bool")


def test_collection_to_bool_skips_assign_and_return_counts() -> None:
    rule = collection_to_bool_rule()
    assert not rule.detect("ready = len(items)\n", "sample.py")
    assert not rule.detect("count: int = len(items)\n", "sample.py")
    assert not rule.detect("def size(items):\n    return len(items)\n", "sample.py")


def test_collection_to_bool_flags_truthiness_contexts() -> None:
    rule = collection_to_bool_rule()
    hits = rule.detect("if len(items):\n    process(items)\n", "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "bool(items)" in hits[0].suggestion.after

    hits = rule.detect("while not len(items):\n    break\n", "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "bool(items)" in hits[0].suggestion.after
