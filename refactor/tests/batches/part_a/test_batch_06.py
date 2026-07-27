from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "max-min-default",
        "largest = max(values) if values else 0\n",
        "max(values, default = 0)",
    ),
    (
        "merge-assign-and-aug-assign",
        "merge_assign_and_aug_assign = 1\n",
        "Review Sourcery pattern for merge-assign-and-aug-assign",
    ),
    (
        "merge-comparisons",
        "if low < value and value < high:\n    pass\n",
        "low < value < high",
    ),
    (
        "merge-dict-assign",
        'data = {"merge_dict_assign": 1}\n',
        "Review dictionary pattern for merge-dict-assign",
    ),
    (
        "merge-duplicate-blocks",
        "merge_duplicate_blocks = 1\n",
        "Review Sourcery pattern for merge-duplicate-blocks",
    ),
    (
        "merge-else-if-into-elif",
        "if merge_else_if_into_elif:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for merge-else-if-into-elif",
    ),
    (
        "merge-except-handler",
        'raise RuntimeError("merge_except_handler")\n',
        "Review exception pattern for merge-except-handler",
    ),
    (
        "merge-is-instance",
        "if isinstance(value, str) or isinstance(value, bytes):\n    pass\n",
        "isinstance(value, (str, bytes))",
    ),
    (
        "merge-isinstance",
        "if isinstance(value, int) or isinstance(value, float):\n    pass\n",
        "isinstance(value, (int, float))",
    ),
    (
        "merge-list-append",
        'items = ["merge_list_append"]\n',
        "Review collection pattern for merge-list-append",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_06_detects_fixture(
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
def test_batch_06_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
