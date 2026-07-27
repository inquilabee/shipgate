from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "swap-variable",
        "swap_variable = 1\n",
        "Review Sourcery pattern for swap-variable",
    ),
    (
        "switch",
        "if switch:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for switch",
    ),
    (
        "ternary-to-if-expression",
        "if ternary_to_if_expression:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for ternary-to-if-expression",
    ),
    (
        "unwrap-iterable-construction",
        "items = list([1, 2, 3])\n",
        "[1, 2, 3]",
    ),
    (
        "use",
        "# use: comment-only placeholder\n",
        "use is registered as comment-only",
    ),
    (
        "use-any",
        "use_any = 1\n",
        "Review Sourcery pattern for use-any",
    ),
    (
        "use-assigned-variable",
        "use_assigned_variable = 1\n",
        "Review Sourcery pattern for use-assigned-variable",
    ),
    (
        "use-contextlib-suppress",
        "use_contextlib_suppress = 1\n",
        "Review Sourcery pattern for use-contextlib-suppress",
    ),
    (
        "use-count",
        "total = sum(1 for item in items if item == needle)\n",
        "items.count(needle)",
    ),
    (
        "use-datetime-now-not-today",
        "stamp = datetime.today()\n",
        "datetime.now()",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_13_detects_fixture(
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
def test_batch_13_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
