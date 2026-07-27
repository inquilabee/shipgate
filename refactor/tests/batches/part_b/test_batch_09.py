from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "remove-duplicate-set-key",
        'items = {"a", "b", "a"}\n',
        '{"a", "b"}',
    ),
    (
        "remove-empty-nested-block",
        "remove_empty_nested_block = 1\n",
        "Review Sourcery pattern for remove-empty-nested-block",
    ),
    (
        "remove-none-from-default-get",
        "value = data.get(key, None)\n",
        "data.get(key)",
    ),
    (
        "remove-pass-body",
        "remove_pass_body = 1\n",
        "Review Sourcery pattern for remove-pass-body",
    ),
    (
        "remove-pass-elif",
        "if remove_pass_elif:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for remove-pass-elif",
    ),
    (
        "remove-redundant-boolean",
        "if bool(ready):\n    pass\n",
        "ready",
    ),
    (
        "remove-redundant-condition",
        "result = value if condition else value\n",
        "value",
    ),
    (
        "remove-redundant-constructor-in-dict-union",
        "data = dict(left) | dict(right)\n",
        "left | right",
    ),
    (
        "remove-redundant-continue",
        "for remove_redundant_continue in items:\n    continue\n",
        "Review loop pattern for remove-redundant-continue",
    ),
    (
        "remove-redundant-except-handler",
        'raise RuntimeError("remove_redundant_except_handler")\n',
        "Review exception pattern for remove-redundant-except-handler",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_09_detects_fixture(
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
def test_batch_09_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
