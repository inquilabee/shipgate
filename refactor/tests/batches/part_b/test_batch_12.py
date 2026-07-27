from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "simplify-single-exception-tuple",
        "try:\n    risky()\nexcept (ValueError,):\n    recover()\n",
        "ValueError",
    ),
    (
        "simplify-string-len-comparison",
        "if len(name) == 0:\n    pass\n",
        "not name",
    ),
    (
        "simplify-substring-search",
        'if text.find("needle") != -1:\n    pass\n',
        '"needle" in text',
    ),
    (
        "skip-sorted-list-construction",
        "items = sorted(list(values))\n",
        "sorted(values)",
    ),
    (
        "split-or-ifs",
        "if split_or_ifs:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for split-or-ifs",
    ),
    (
        "str-prefix-suffix",
        'if name[:3] == "pre":\n    pass\n',
        'name.startswith("pre")',
    ),
    (
        "sum-comprehension",
        "total = sum([item.count for item in items])\n",
        "sum(item.count for item in items)",
    ),
    (
        "swap-if-else-branches",
        "result = left if not condition else right\n",
        "right if condition else left",
    ),
    (
        "swap-if-expression",
        "result = yes if not condition else no\n",
        "no if condition else yes",
    ),
    (
        "swap-nested-ifs",
        "if swap_nested_ifs:\n    result = True\nelse:\n    result = False\n",
        "Review conditional pattern for swap-nested-ifs",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_12_detects_fixture(
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
def test_batch_12_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
