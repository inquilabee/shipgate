from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

CASES = (
    (
        "swap-variable",
        "temp = left\nleft = right\nright = temp\n",
        "left, right = right, left",
    ),
    (
        "switch",
        'if status == "open":\n    handle_open()\nelif status == "closed":\n    handle_closed()\n',
        "match status",
    ),
    (
        "ternary-to-if-expression",
        "if condition:\n    result = left\nelse:\n    result = right\n",
        "left if condition else right",
    ),
    (
        "unwrap-iterable-construction",
        "items = list([1, 2, 3])\n",
        "[1, 2, 3]",
    ),
    (
        "use",
        "# use: comment-only placeholder\n",
        "use is registered as comment-only",
    ),
    (
        "use-any",
        "matched = bool([item.ready for item in items])\n",
        "any(item.ready for item in items)",
    ),
    (
        "use-assigned-variable",
        (
            "def total(wardrobe):\n"
            "    for item in wardrobe:\n"
            "        count = wardrobe[item]\n"
            "        add_to_total(wardrobe[item])\n"
        ),
        "add_to_total(count)",
    ),
    (
        "use-contextlib-suppress",
        "try:\n    risky()\nexcept ValueError:\n    pass\n",
        "with suppress(ValueError):",
    ),
    (
        "use-count",
        "total = sum(1 for item in items if item == needle)\n",
        "items.count(needle)",
    ),
    (
        "use-datetime-now-not-today",
        "stamp = datetime.today()\n",
        "datetime.now()",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_swap_use_datetime_detects_fixture(
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
def test_swap_use_datetime_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
