from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "useless-else-on-loop",
        "if useless_else_on_loop:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for useless-else-on-loop",
    ),
    (
        "while-guard-to-condition",
        "if while_guard_to_condition:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for while-guard-to-condition",
    ),
    (
        "while-to-for",
        "for while_to_for in items:\n    continue\n",
        "Review loop pattern for while-to-for",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_15_detects_fixture(
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
def test_batch_15_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
