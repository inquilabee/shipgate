from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "remove-redundant-exception",
        'raise RuntimeError("remove_redundant_exception")\n',
        "Review exception pattern for remove-redundant-exception",
    ),
    (
        "remove-redundant-if",
        "if condition:\n    return True\nelse:\n    return False\n",
        "return condition",
    ),
    (
        "remove-redundant-path-exists",
        "remove_redundant_path_exists = 1\n",
        "Review Sourcery pattern for remove-redundant-path-exists",
    ),
    (
        "remove-unnecessary-cast",
        "value = cast(int, raw)\n",
        "raw",
    ),
    (
        "remove-unnecessary-else",
        "if ready:\n    return result\nelse:\n    return fallback\n",
        "return fallback",
    ),
    (
        "remove-unused-enumerate",
        "remove_unused_enumerate = 1\n",
        "Review Sourcery pattern for remove-unused-enumerate",
    ),
    (
        "replace-apply-with-method-call",
        "names = series.apply(str.lower)\n",
        "series.str.lower()",
    ),
    (
        "replace-apply-with-numpy-operation",
        "roots = series.apply(np.sqrt)\n",
        "np.sqrt(series)",
    ),
    (
        "replace-dict-items-with-values",
        'data = {"replace_dict_items_with_values": 1}\n',
        "Review dictionary pattern for replace-dict-items-with-values",
    ),
    (
        "replace-interpolation-with-fstring",
        'value = "replace_interpolation_with_fstring"\n',
        "Review string pattern for replace-interpolation-with-fstring",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_10_detects_fixture(
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
def test_batch_10_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
