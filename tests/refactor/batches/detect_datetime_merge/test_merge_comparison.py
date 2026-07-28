from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

CASES = (
    (
        "max-min-default",
        "largest = max(values) if values else 0\n",
        "max(values, default = 0)",
    ),
    (
        "merge-assign-and-aug-assign",
        "count = count + step\n",
        "count += step",
    ),
    (
        "merge-comparisons",
        "if low < value and value < high:\n    pass\n",
        "low < value < high",
    ),
    (
        "merge-dict-assign",
        'data["a"] = 1\ndata["b"] = 2\n',
        'data.update({"a": 1, "b": 2})',
    ),
    (
        "merge-duplicate-blocks",
        "if ready:\n    finish()\nelse:\n    finish()\n",
        "finish()",
    ),
    (
        "merge-else-if-into-elif",
        "if ready:\n    result = True\nelse:\n    if fallback:\n        result = False\n",
        "elif fallback",
    ),
    (
        "merge-except-handler",
        "try:\n    risky()\nexcept ValueError:\n    recover()\nexcept TypeError:\n    recover()\n",
        "except ValueError, TypeError",
    ),
    (
        "merge-is-instance",
        "if isinstance(value, str) or isinstance(value, bytes):\n    pass\n",
        "isinstance(value, (str, bytes))",
    ),
    (
        "merge-isinstance",
        "if isinstance(value, int) or isinstance(value, float):\n    pass\n",
        "isinstance(value, (int, float))",
    ),
    (
        "merge-list-append",
        "items.append(first)\nitems.append(second)\n",
        "items.extend([first, second])",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_merge_comparison_detects_fixture(
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
def test_merge_comparison_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
