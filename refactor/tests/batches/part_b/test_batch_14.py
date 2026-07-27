from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "use-dict-items",
        "for key in data:\n    value = data[key]\n    consume(value)\n",
        "for key, value in data.items()",
    ),
    (
        "use-dictionary-union",
        "merged = dict(left, **right)\n",
        "left | right",
    ),
    (
        "use-file-iterator",
        "lines = handle.readlines()\n",
        "handle",
    ),
    (
        "use-getitem-for-re-match-groups",
        "value = match.group(1)\n",
        "match[1]",
    ),
    (
        "use-isna",
        "mask = series == None\n",
        "series.isna()",
    ),
    (
        "use-itertools-product",
        "use_itertools_product = 1\n",
        "Review Sourcery pattern for use-itertools-product",
    ),
    (
        "use-join",
        "value = first + middle + last\n",
        '"".join([first, middle, last])',
    ),
    (
        "use-named-expression",
        "use_named_expression = 1\n",
        "Review Sourcery pattern for use-named-expression",
    ),
    (
        "use-or-for-fallback",
        "result = value if value else fallback\n",
        "value or fallback",
    ),
    (
        "use-string-remove-affix",
        "value = text[len(prefix):]\n",
        "text.removeprefix(prefix)",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_14_detects_fixture(
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
def test_batch_14_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
