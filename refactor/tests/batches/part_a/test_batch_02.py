from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "aware-datetime-for-utc",
        "for aware_datetime_for_utc in items:\n    continue\n",
        "Review loop pattern for aware-datetime-for-utc",
    ),
    (
        "break-or-continue-outside-loop",
        "for break_or_continue_outside_loop in items:\n    continue\n",
        "Review loop pattern for break-or-continue-outside-loop",
    ),
    (
        "chain-compares",
        "if low <= value and value <= high:\n    pass\n",
        "low <= value <= high",
    ),
    (
        "class-extract-method",
        "class Example:\n    def class_extract_method(self):\n        return 1\n",
        "Review method extraction pattern for class-extract-method",
    ),
    (
        "class-method-first-arg-name",
        "class Example:\n    def class_method_first_arg_name(self):\n        return 1\n",
        "Review method extraction pattern for class-method-first-arg-name",
    ),
    (
        "collection-builtin-to-comprehension",
        "mapping = dict((key, value) for key, value in pairs)\n",
        "{key: value for key, value in pairs}",
    ),
    (
        "collection-to-bool",
        "ready = len(items)\n",
        "bool(items)",
    ),
    (
        "compare-via-equals",
        "if left.__eq__(right):\n    pass\n",
        "left == right",
    ),
    (
        "comprehension-to-generator",
        "matched = any([item.ready for item in items])\n",
        "any(item.ready for item in items)",
    ),
    (
        "convert-any-to-in",
        "convert_any_to_in = 1\n",
        "Review Sourcery pattern for convert-any-to-in",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_02_detects_fixture(
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
def test_batch_02_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
