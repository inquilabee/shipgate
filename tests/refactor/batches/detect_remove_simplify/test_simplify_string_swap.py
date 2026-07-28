from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

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
        "if left or right:\n    run()\n",
        "if right",
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
        "if outer:\n    if inner:\n        result = True\n",
        "outer and inner",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_simplify_string_swap_detects_fixture(
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
def test_simplify_string_swap_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
