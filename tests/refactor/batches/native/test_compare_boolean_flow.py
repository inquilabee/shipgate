from __future__ import annotations

import pytest

from refactor.inventory import load_inventory
from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

RULE_IDS = (
    "none-compare",
    "boolean-if-exp-identity",
    "simplify-boolean-comparison",
    "merge-nested-ifs",
    "inline-immediately-returned-variable",
    "use-next",
    "identity-comprehension",
)

SAFE_APPLY_FALSE_IDS = (
    "none-compare",
    "boolean-if-exp-identity",
    "simplify-boolean-comparison",
    "merge-nested-ifs",
    "inline-immediately-returned-variable",
    "use-next",
    "identity-comprehension",
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "source", "expected_fragment"),
    [
        ("none-compare", "if x == None:\n    pass\n", "is None"),
        ("boolean-if-exp-identity", "y = True if cond else False\n", "cond"),
        (
            "simplify-boolean-comparison",
            "if x == True:\n    pass\n",
            "x",
        ),
        (
            "merge-nested-ifs",
            "if a:\n    if b:\n        pass\n",
            "if a and b:",
        ),
        (
            "inline-immediately-returned-variable",
            "def f():\n    x = 1 + 2\n    return x\n",
            "return 1 + 2",
        ),
        (
            "use-next",
            "def f():\n    for x in xs:\n        return x\n",
            "next(iter(xs))",
        ),
        (
            "identity-comprehension",
            "items = [x for x in xs]\n",
            "list(xs)",
        ),
    ],
)
def test_compare_boolean_flow_detects(
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


def test_none_compare_detects_not_equal(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["none-compare"]
    hits = rule.detect("if x != None:\n    pass\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "is not None" in hits[0].suggestion.after


def test_boolean_if_exp_identity_detects_inverse(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["boolean-if-exp-identity"]
    hits = rule.detect("y = False if cond else True\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "not cond" in hits[0].suggestion.after


def test_simplify_boolean_comparison_detects_false(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["simplify-boolean-comparison"]
    hits = rule.detect("if x == False:\n    pass\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "not x" in hits[0].suggestion.after


@pytest.mark.parametrize("rule_id", SAFE_APPLY_FALSE_IDS)
def test_compare_boolean_flow_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is not ApplyMode.AUTO


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_compare_boolean_flow_inventory_native(rule_id: str) -> None:
    by_id = {entry.id: entry for entry in load_inventory()}
    assert by_id[rule_id].status == "native"
