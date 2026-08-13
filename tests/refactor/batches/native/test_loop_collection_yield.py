from __future__ import annotations

import pytest

from refactor.inventory import load_inventory
from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

RULE_IDS = (
    "for-index-replacement",
    "collection-into-set",
    "default-mutable-arg",
    "remove-unreachable-code",
    "yield-from",
    "bin-op-identity",
)

SAFE_APPLY_TRUE_IDS = (
    "collection-into-set",
    "yield-from",
    "bin-op-identity",
)

SAFE_APPLY_FALSE_IDS = (
    "for-index-replacement",
    "default-mutable-arg",
    "remove-unreachable-code",
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "source", "expected_fragment"),
    [
        (
            "for-index-replacement",
            "for i in range(len(xs)):\n    print(xs[i])\n",
            "enumerate(xs)",
        ),
        (
            "collection-into-set",
            "if x in [1, 2, 3]:\n    pass\n",
            "x in {1, 2, 3}",
        ),
        (
            "default-mutable-arg",
            "def f(items=[]):\n    pass\n",
            "items is None",
        ),
        (
            "remove-unreachable-code",
            "def f():\n    return 1\n    x = 2\n",
            "return 1",
        ),
        (
            "yield-from",
            "def f():\n    for x in ys:\n        yield x\n",
            "yield from ys",
        ),
        (
            "bin-op-identity",
            "y = x + 0\n",
            "y = x",
        ),
    ],
)
def test_loop_collection_yield_detects(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected_fragment: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(source, "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert expected_fragment in hits[0].suggestion.after


def test_collection_into_set_detects_string_literals(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["collection-into-set"]
    hits = rule.detect('if status in ["a", "b"]:\n    pass\n', "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert '{"a", "b"}' in hits[0].suggestion.after


def test_default_mutable_arg_detects_dict(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["default-mutable-arg"]
    hits = rule.detect("def f(opts={}):\n    pass\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "opts is None" in hits[0].suggestion.after


def test_bin_op_identity_detects_multiply(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["bin-op-identity"]
    hits = rule.detect("y = x * 1\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "y = x" in hits[0].suggestion.after


def test_default_mutable_arg_kind_is_suggestion(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    from refactor.protocol import RuleKind

    rule = rules_by_id["default-mutable-arg"]
    assert rule.kind is RuleKind.SUGGESTION


@pytest.mark.parametrize("rule_id", SAFE_APPLY_TRUE_IDS)
def test_loop_collection_yield_safe_apply_true(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is ApplyMode.AUTO


@pytest.mark.parametrize("rule_id", SAFE_APPLY_FALSE_IDS)
def test_loop_collection_yield_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is not ApplyMode.AUTO


def test_yield_from_skips_async_functions(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["yield-from"]
    source = "async def f():\n    for x in ys:\n        yield x\n"
    assert not rule.detect(source, "sample.py")
    assert rule.apply(source, []) in (None, source)


def test_default_mutable_arg_set_literal_does_not_raise(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["default-mutable-arg"]
    hits = rule.detect("def f(xs={1}):\n    pass\n", "sample.py")
    assert len(hits) == 1
    assert hits[0].suggestion is not None
    assert "set()" in hits[0].suggestion.after


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_loop_collection_yield_inventory_native(rule_id: str) -> None:
    by_id = {entry.id: entry for entry in load_inventory()}
    assert by_id[rule_id].status == "native"
