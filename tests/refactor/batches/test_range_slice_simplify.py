from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.protocol import ApplyMode
from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

RULE_IDS = (
    "remove-zero-from-range",
    "remove-unit-step-from-range",
    "remove-redundant-slice-index",
    "simplify-negative-index",
    "square-identity",
    "simplify-division",
    "remove-str-from-print",
    "remove-str-from-fstring",
    "remove-redundant-fstring",
    "remove-assert-true",
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "source", "expected_fragment"),
    [
        ("remove-zero-from-range", "for i in range(0, 10):\n    pass\n", "range(10)"),
        (
            "remove-unit-step-from-range",
            "for i in range(0, 10, 1):\n    pass\n",
            "range(0, 10)",
        ),
        ("remove-redundant-slice-index", "xs[0:n]\n", "xs[:n]"),
        ("simplify-negative-index", "xs[len(xs) - 1]\n", "xs[-1]"),
        ("square-identity", "y = x * x\n", "x ** 2"),
        ("simplify-division", "y = x / 1\n", "x"),
        ("remove-str-from-print", "print(str(x))\n", "print(x)"),
        ("remove-str-from-fstring", 's = f"{str(x)}"\n', "{x}"),
        ("remove-redundant-fstring", 's = f"hello"\n', '"hello"'),
        (
            "remove-assert-true",
            "def f():\n    x = 1\n    assert True\n",
            "x = 1",
        ),
    ],
)
def test_range_slice_simplify_detects(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected_fragment: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(source, "sample.py")
    assert len(hits) >= 1
    assert hits[0].suggestion is not None
    assert expected_fragment in hits[0].suggestion.after


@pytest.mark.parametrize("rule_id", RULE_IDS)
def test_range_slice_simplify_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is not ApplyMode.AUTO
