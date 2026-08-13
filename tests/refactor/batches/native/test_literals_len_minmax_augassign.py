from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

RULE_IDS = (
    "dict-literal",
    "tuple-literal",
    "remove-redundant-pass",
    "use-len",
    "min-max-identity",
    "aug-assign",
)

SAFE_APPLY_TRUE_IDS = (
    "dict-literal",
    "tuple-literal",
    "remove-redundant-pass",
    "use-len",
    "min-max-identity",
)

SAFE_APPLY_FALSE_IDS: tuple[str, ...] = ("aug-assign",)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "source", "expected_fragment"),
    [
        ("dict-literal", "x = dict()\n", "{}"),
        ("tuple-literal", "x = tuple()\n", "()"),
        (
            "remove-redundant-pass",
            "def f():\n    x = 1\n    pass\n",
            "x = 1",
        ),
        ("use-len", "if len(items) == 0:\n    pass\n", "not items"),
        (
            "min-max-identity",
            "z = a if a < b else b\n",
            "min(a, b)",
        ),
        ("aug-assign", "x = x + 1\n", "+="),
    ],
)
def test_literals_len_minmax_augassign_detects(
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


def test_min_max_identity_detects_max(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["min-max-identity"]
    hits = rule.detect("z = a if a > b else b\n", "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert "max(a, b)" in hits[0].suggestion.after


@pytest.mark.parametrize("rule_id", SAFE_APPLY_TRUE_IDS)
def test_literals_len_minmax_augassign_safe_apply_true(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is ApplyMode.AUTO


@pytest.mark.parametrize("rule_id", SAFE_APPLY_FALSE_IDS)
def test_literals_len_minmax_augassign_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is not ApplyMode.AUTO


def test_use_len_skips_empty_and_starred_calls(rules_by_id: dict[str, RefactorRule]) -> None:
    rule = rules_by_id["use-len"]
    assert not rule.detect("if len() == 0:\n    pass\n", "sample.py")
    assert not rule.detect("if len(*items) == 0:\n    pass\n", "sample.py")
