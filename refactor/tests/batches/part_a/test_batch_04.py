from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "for-append-to-extend",
        "for item in items:\n    result.append(item)\n",
        "result.extend(items)",
    ),
    (
        "for-index-underscore",
        "for index, _ in enumerate(items):\n    consume(index)\n",
        "for index in range(len(items))",
    ),
    (
        "guard",
        "if guard:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for guard",
    ),
    (
        "hoist-if-from-if",
        "if outer:\n    if inner:\n        result = True\n",
        "outer and inner",
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
        "if ready:\n    prepare()\n    finish()\nelse:\n    recover()\n    finish()\n",
        "finish()",
    ),
    (
        "hoist-statement-from-loop",
        "for hoist_statement_from_loop in items:\n    continue\n",
        "Review loop pattern for hoist-statement-from-loop",
    ),
    (
        "inline-immediately-yielded-variable",
        "value = build()\nyield value\n",
        "yield build()",
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
