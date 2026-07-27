from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

SAFE_APPLY_BATCH_B_IDS = (
    "use-len",
    "min-max-identity",
    "none-compare",
    "boolean-if-exp-identity",
    "simplify-boolean-comparison",
    "collection-into-set",
    "yield-from",
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "before", "after"),
    [
        ("use-len", "if len(items) == 0:\n    pass\n", "if not items:\n    pass\n"),
        ("min-max-identity", "z = a if a < b else b\n", "z = min(a, b)\n"),
        ("none-compare", "if x == None:\n    pass\n", "if x is None:\n    pass\n"),
        ("boolean-if-exp-identity", "y = True if cond else False\n", "y = cond\n"),
        ("simplify-boolean-comparison", "if x == True:\n    pass\n", "if x:\n    pass\n"),
        (
            "collection-into-set",
            "if x in [1, 2, 3]:\n    pass\n",
            "if x in {1, 2, 3}:\n    pass\n",
        ),
        (
            "yield-from",
            "def f():\n    for x in ys:\n        yield x\n",
            "def f():\n    yield from ys\n",
        ),
    ],
)
def test_safe_apply_round_trip(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    before: str,
    after: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.safe_apply is True
    hits = rule.detect(before, "sample.py")
    assert len(hits) >= 1
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "sample.py") == []


def test_none_compare_round_trip_not_equal(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["none-compare"]
    before = "if x != None:\n    pass\n"
    after = "if x is not None:\n    pass\n"
    hits = rule.detect(before, "sample.py")
    assert len(hits) >= 1
    assert "is not None" in hits[0].message
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "sample.py") == []


def test_min_max_identity_round_trip_max(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["min-max-identity"]
    before = "z = a if a > b else b\n"
    after = "z = max(a, b)\n"
    hits = rule.detect(before, "sample.py")
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "sample.py") == []


def test_boolean_if_exp_identity_round_trip_inverse(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["boolean-if-exp-identity"]
    before = "y = False if cond else True\n"
    after = "y = not cond\n"
    hits = rule.detect(before, "sample.py")
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "sample.py") == []


def test_simplify_boolean_comparison_round_trip_false(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["simplify-boolean-comparison"]
    before = "if x == False:\n    pass\n"
    after = "if not x:\n    pass\n"
    hits = rule.detect(before, "sample.py")
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert rule.detect(rewritten or "", "sample.py") == []


@pytest.mark.parametrize("rule_id", SAFE_APPLY_BATCH_B_IDS)
def test_safe_apply_batch_b_enabled(rules_by_id: dict[str, RefactorRule], rule_id: str) -> None:
    rule = rules_by_id[rule_id]
    assert rule.safe_apply is True
