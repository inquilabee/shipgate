from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "inline-variable",
        "inline_variable = 1\n",
        "Review Sourcery pattern for inline-variable",
    ),
    (
        "instance-method-first-arg-name",
        "class Example:\n    def instance_method_first_arg_name(self):\n        return 1\n",
        "Review method extraction pattern for instance-method-first-arg-name",
    ),
    (
        "introduce-default-else",
        "if introduce_default_else:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for introduce-default-else",
    ),
    (
        "invert-any-all",
        "invert_any_all = 1\n",
        "Review Sourcery pattern for invert-any-all",
    ),
    (
        "invert-any-all-body",
        "invert_any_all_body = 1\n",
        "Review Sourcery pattern for invert-any-all-body",
    ),
    (
        "last-if-guard",
        "if last_if_guard:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for last-if-guard",
    ),
    (
        "lift-duplicated-conditional",
        "if lift_duplicated_conditional:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for lift-duplicated-conditional",
    ),
    (
        "lift-return-into-if",
        "if lift_return_into_if:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for lift-return-into-if",
    ),
    (
        "list-comprehension",
        'items = ["list_comprehension"]\n',
        "Review collection pattern for list-comprehension",
    ),
    (
        "low-code-quality",
        "# low-code-quality: comment-only placeholder\n",
        "low-code-quality is registered as comment-only",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_05_detects_fixture(
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
def test_batch_05_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
