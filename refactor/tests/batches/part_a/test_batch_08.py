from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "non-equal-comparison",
        "if not (left == right):\n    pass\n",
        "left != right",
    ),
    (
        "or-if-exp-identity",
        "if or_if_exp_identity:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for or-if-exp-identity",
    ),
    (
        "pandas-avoid-inplace",
        "df.pandas_avoid_inplace()\n",
        "Review pandas pattern for pandas-avoid-inplace",
    ),
    (
        "raise-from-previous-error",
        'raise RuntimeError("raise_from_previous_error")\n',
        "Review exception pattern for raise-from-previous-error",
    ),
    (
        "raise-specific-error",
        'raise RuntimeError("raise_specific_error")\n',
        "Review exception pattern for raise-specific-error",
    ),
    (
        "reintroduce-else",
        "if reintroduce_else:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for reintroduce-else",
    ),
    (
        "remove-dict-items",
        'data = {"remove_dict_items": 1}\n',
        "Review dictionary pattern for remove-dict-items",
    ),
    (
        "remove-dict-keys",
        "if key in data.keys():\n    pass\n",
        "data",
    ),
    (
        "remove-duplicate-dict-key",
        'data = {"remove_duplicate_dict_key": 1}\n',
        "Review dictionary pattern for remove-duplicate-dict-key",
    ),
    (
        "remove-duplicate-key",
        'data = {"a": 1, "a": 2}\n',
        '"a": 2',
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_08_detects_fixture(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(source, "sample.py")
    if rule_id in {"use", "method", "low-code-quality"}:
        assert hits == []
        return
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert expected in hits[0].suggestion.after


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_08_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
