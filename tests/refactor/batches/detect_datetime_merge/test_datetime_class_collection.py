from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

CASES = (
    (
        "aware-datetime-for-utc",
        "stamp = datetime.utcnow()\n",
        "datetime.now(UTC)",
    ),
    (
        "break-or-continue-outside-loop",
        "break\n",
        "",
    ),
    (
        "chain-compares",
        "if low <= value and value <= high:\n    pass\n",
        "low <= value <= high",
    ),
    (
        "class-extract-method",
        "class Example:\n    def run(self):\n"
        "        prepare()\n        execute()\n        finish()\n",
        "self._extracted_method()",
    ),
    (
        "class-method-first-arg-name",
        "class Example:\n    @classmethod\n    def build(self):\n        return self()\n",
        "def build(cls)",
    ),
    (
        "collection-builtin-to-comprehension",
        "mapping = dict((key, value) for key, value in pairs)\n",
        "{key: value for key, value in pairs}",
    ),
    (
        "collection-to-bool",
        "if len(items):\n    process(items)\n",
        "bool(items)",
    ),
    (
        "compare-via-equals",
        "if left.__eq__(right):\n    pass\n",
        "left == right",
    ),
    (
        "comprehension-to-generator",
        "matched = any([item.ready for item in items])\n",
        "any(item.ready for item in items)",
    ),
    (
        "convert-any-to-in",
        "matched = any(item == needle for item in items)\n",
        "needle in items",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_datetime_class_collection_detects_fixture(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(source, "sample.py")
    skip = rule_id in {"use", "method", "low-code-quality", "class-extract-method"}
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
def test_datetime_class_collection_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
