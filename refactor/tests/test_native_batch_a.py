from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

BATCH_A_IDS = (
    "dict-literal",
    "tuple-literal",
    "remove-redundant-pass",
    "use-len",
    "min-max-identity",
    "aug-assign",
)

BATCH_A_SAFE_APPLY_TRUE = (
    "dict-literal",
    "tuple-literal",
    "remove-redundant-pass",
    "use-len",
    "min-max-identity",
    "aug-assign",
)

BATCH_A_SAFE_APPLY_FALSE: tuple[str, ...] = ()


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
def test_native_batch_a_detects(
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


@pytest.mark.parametrize("rule_id", BATCH_A_SAFE_APPLY_TRUE)
def test_native_batch_a_safe_apply_true(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.safe_apply is True


@pytest.mark.parametrize("rule_id", BATCH_A_SAFE_APPLY_FALSE)
def test_native_batch_a_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.safe_apply is False
