from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "simplify-single-exception-tuple",
        'raise RuntimeError("simplify_single_exception_tuple")\n',
        "Review exception pattern for simplify-single-exception-tuple",
    ),
    (
        "simplify-string-len-comparison",
        'value = "simplify_string_len_comparison"\n',
        "Review string pattern for simplify-string-len-comparison",
    ),
    (
        "simplify-substring-search",
        'value = "simplify_substring_search"\n',
        "Review string pattern for simplify-substring-search",
    ),
    (
        "skip-sorted-list-construction",
        'items = ["skip_sorted_list_construction"]\n',
        "Review collection pattern for skip-sorted-list-construction",
    ),
    (
        "split-or-ifs",
        "if split_or_ifs:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for split-or-ifs",
    ),
    (
        "str-prefix-suffix",
        'value = "str_prefix_suffix"\n',
        "Review string pattern for str-prefix-suffix",
    ),
    (
        "sum-comprehension",
        "sum_comprehension = 1\n",
        "Review Sourcery pattern for sum-comprehension",
    ),
    (
        "swap-if-else-branches",
        "if swap_if_else_branches:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for swap-if-else-branches",
    ),
    (
        "swap-if-expression",
        "if swap_if_expression:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for swap-if-expression",
    ),
    (
        "swap-nested-ifs",
        "if swap_nested_ifs:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for swap-nested-ifs",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_12_detects_fixture(
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
def test_batch_12_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
