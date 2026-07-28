from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

CASES = (
    (
        "useless-else-on-loop",
        "for item in items:\n    process(item)\nelse:\n    report()\n",
        "report()",
    ),
    (
        "while-guard-to-condition",
        "while True:\n    if not ready:\n        break\n    process()\n",
        "while ready",
    ),
    (
        "while-to-for",
        "i = 0\nwhile i < len(items):\n    consume(items[i])\n    i += 1\n",
        "for i in range(len(items))",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_loop_while_detects_fixture(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(source, "sample.py")
    skip = rule_id in {"use", "method", "low-code-quality"}
    assert (
        (not hits)
        if skip
        else (
            len(hits) >= 1
            and hits[0].suggestion is not None
            and expected in hits[0].suggestion.after
        )
    )


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_loop_while_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
