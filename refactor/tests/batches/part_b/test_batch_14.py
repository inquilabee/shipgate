from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "use-dict-items",
        'data = {"use_dict_items": 1}\n',
        "Review dictionary pattern for use-dict-items",
    ),
    (
        "use-dictionary-union",
        'data = {"use_dictionary_union": 1}\n',
        "Review dictionary pattern for use-dictionary-union",
    ),
    (
        "use-file-iterator",
        "use_file_iterator = 1\n",
        "Review Sourcery pattern for use-file-iterator",
    ),
    (
        "use-getitem-for-re-match-groups",
        "value = match.group(1)\n",
        "match[1]",
    ),
    (
        "use-isna",
        "df.use_isna()\n",
        "Review pandas pattern for use-isna",
    ),
    (
        "use-itertools-product",
        "use_itertools_product = 1\n",
        "Review Sourcery pattern for use-itertools-product",
    ),
    (
        "use-join",
        'value = "use_join"\n',
        "Review string pattern for use-join",
    ),
    (
        "use-named-expression",
        "use_named_expression = 1\n",
        "Review Sourcery pattern for use-named-expression",
    ),
    (
        "use-or-for-fallback",
        "for use_or_for_fallback in items:\n    continue\n",
        "Review loop pattern for use-or-for-fallback",
    ),
    (
        "use-string-remove-affix",
        'value = "use_string_remove_affix"\n',
        "Review string pattern for use-string-remove-affix",
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
