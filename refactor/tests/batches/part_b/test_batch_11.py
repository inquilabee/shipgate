from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "return-identity",
        "return_identity = 1\n",
        "Review Sourcery pattern for return-identity",
    ),
    (
        "return-or-yield-outside-function",
        "return_or_yield_outside_function = 1\n",
        "Review Sourcery pattern for return-or-yield-outside-function",
    ),
    (
        "set-comprehension",
        "items = set(item.name for item in records)\n",
        "{item.name for item in records}",
    ),
    (
        "simplify-constant-sum",
        "total = 2 + 3\n",
        "5",
    ),
    (
        "simplify-dictionary-update",
        'data = {"simplify_dictionary_update": 1}\n',
        "Review dictionary pattern for simplify-dictionary-update",
    ),
    (
        "simplify-empty-collection-comparison",
        "if items == []:\n    pass\n",
        "not items",
    ),
    (
        "simplify-fstring-formatting",
        'value = "simplify_fstring_formatting"\n',
        "Review string pattern for simplify-fstring-formatting",
    ),
    (
        "simplify-generator",
        "if simplify_generator:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for simplify-generator",
    ),
    (
        "simplify-len-comparison",
        "if len(items) > 0:\n    pass\n",
        "items",
    ),
    (
        "simplify-numeric-comparison",
        "if simplify_numeric_comparison:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for simplify-numeric-comparison",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_11_detects_fixture(
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
def test_batch_11_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
