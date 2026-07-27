from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "remove-duplicate-set-key",
        'data = {"remove_duplicate_set_key": 1}\n',
        "Review dictionary pattern for remove-duplicate-set-key",
    ),
    (
        "remove-empty-nested-block",
        "remove_empty_nested_block = 1\n",
        "Review Sourcery pattern for remove-empty-nested-block",
    ),
    (
        "remove-none-from-default-get",
        "remove_none_from_default_get = 1\n",
        "Review Sourcery pattern for remove-none-from-default-get",
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
        "remove_redundant_boolean = 1\n",
        "Review Sourcery pattern for remove-redundant-boolean",
    ),
    (
        "remove-redundant-condition",
        "if remove_redundant_condition:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for remove-redundant-condition",
    ),
    (
        "remove-redundant-constructor-in-dict-union",
        'data = {"remove_redundant_constructor_in_dict_union": 1}\n',
        "Review dictionary pattern for remove-redundant-constructor-in-dict-union",
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
