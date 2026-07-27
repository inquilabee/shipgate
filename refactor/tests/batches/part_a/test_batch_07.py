from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "merge-list-appends-into-extend",
        'items = ["merge_list_appends_into_extend"]\n',
        "Review collection pattern for merge-list-appends-into-extend",
    ),
    (
        "merge-list-extend",
        'items = ["merge_list_extend"]\n',
        "Review collection pattern for merge-list-extend",
    ),
    (
        "merge-repeated-ifs",
        "if merge_repeated_ifs:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for merge-repeated-ifs",
    ),
    (
        "merge-set-add",
        'items = ["merge_set_add"]\n',
        "Review collection pattern for merge-set-add",
    ),
    (
        "method",
        "# method: comment-only placeholder\n",
        "method is registered as comment-only",
    ),
    (
        "missing-dict-items",
        'data = {"missing_dict_items": 1}\n',
        "Review dictionary pattern for missing-dict-items",
    ),
    (
        "move-assign",
        "move_assign = 1\n",
        "Review Sourcery pattern for move-assign",
    ),
    (
        "move-assign-in-block",
        "move_assign_in_block = 1\n",
        "Review Sourcery pattern for move-assign-in-block",
    ),
    (
        "no-conditionals-in-tests",
        "if no_conditionals_in_tests:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for no-conditionals-in-tests",
    ),
    (
        "no-loop-in-tests",
        "for no_loop_in_tests in items:\n    continue\n",
        "Review loop pattern for no-loop-in-tests",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_07_detects_fixture(
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
def test_batch_07_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
