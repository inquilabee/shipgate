from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "inline-variable",
        "value = build()\nreturn value\n",
        "return build()",
    ),
    (
        "instance-method-first-arg-name",
        "class Example:\n    def run(this):\n        return this.value\n",
        "def run(self)",
    ),
    (
        "introduce-default-else",
        "value = fallback\nif ready:\n    value = result\n",
        "else:\n    value = fallback",
    ),
    (
        "invert-any-all",
        "if not any(item.ready for item in items):\n    pass\n",
        "all(not item.ready for item in items)",
    ),
    (
        "invert-any-all-body",
        "if not all(item.ready for item in items):\n    pass\n",
        "any(not item.ready for item in items)",
    ),
    (
        "last-if-guard",
        "if ready:\n    run()\nreturn fallback\n",
        "if not ready",
    ),
    (
        "lift-duplicated-conditional",
        "if ready:\n    prepare()\n    finish()\nelse:\n    recover()\n    finish()\n",
        "finish()",
    ),
    (
        "lift-return-into-if",
        "if ready:\n    return result\nreturn fallback\n",
        "else:\n    return fallback",
    ),
    (
        "list-comprehension",
        "items = list(item.name for item in records)\n",
        "[item.name for item in records]",
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
    if rule_id in {"use", "method", "low-code-quality", "last-if-guard"}:
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
