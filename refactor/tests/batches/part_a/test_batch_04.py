from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "for-append-to-extend",
        "for for_append_to_extend in items:\n    continue\n",
        "Review loop pattern for for-append-to-extend",
    ),
    (
        "for-index-underscore",
        "for for_index_underscore in items:\n    continue\n",
        "Review loop pattern for for-index-underscore",
    ),
    (
        "guard",
        "if guard:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for guard",
    ),
    (
        "hoist-if-from-if",
        "if hoist_if_from_if:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for hoist-if-from-if",
    ),
    (
        "hoist-loop-from-if",
        "if hoist_loop_from_if:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for hoist-loop-from-if",
    ),
    (
        "hoist-repeated-if-condition",
        "if hoist_repeated_if_condition:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for hoist-repeated-if-condition",
    ),
    (
        "hoist-similar-statement-from-if",
        "if hoist_similar_statement_from_if:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for hoist-similar-statement-from-if",
    ),
    (
        "hoist-statement-from-if",
        "if hoist_statement_from_if:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for hoist-statement-from-if",
    ),
    (
        "hoist-statement-from-loop",
        "for hoist_statement_from_loop in items:\n    continue\n",
        "Review loop pattern for hoist-statement-from-loop",
    ),
    (
        "inline-immediately-yielded-variable",
        "inline_immediately_yielded_variable = 1\n",
        "Review Sourcery pattern for inline-immediately-yielded-variable",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_04_detects_fixture(
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
def test_batch_04_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
