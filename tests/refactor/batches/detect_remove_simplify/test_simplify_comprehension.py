from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "return-identity",
        "result = value if condition else value\n",
        "value",
    ),
    (
        "return-or-yield-outside-function",
        "return value\n",
        "",
    ),
    (
        "set-comprehension",
        "items = set(item.name for item in records)\n",
        "{item.name for item in records}",
    ),
    (
        "simplify-constant-sum",
        'total = sum(1 for book in books if book.author == "Terry Pratchett")\n',
        'sum(bool(book.author == "Terry Pratchett") for book in books)',
    ),
    (
        "simplify-dictionary-update",
        "data.update(other)\n",
        "data |= other",
    ),
    (
        "simplify-empty-collection-comparison",
        "if items == []:\n    pass\n",
        "not items",
    ),
    (
        "simplify-fstring-formatting",
        'value = f"{name!s}"\n',
        'f"{name}"',
    ),
    (
        "simplify-generator",
        "matched = all([item.ready for item in items])\n",
        "all(item.ready for item in items)",
    ),
    (
        "simplify-len-comparison",
        "if len(items) > 0:\n    pass\n",
        "items",
    ),
    (
        "simplify-numeric-comparison",
        "if left - right > 0:\n    pass\n",
        "left > right",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_simplify_comprehension_detects_fixture(
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
def test_simplify_comprehension_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
