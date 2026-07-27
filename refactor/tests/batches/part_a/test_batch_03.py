from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from refactor.registry import RULES

if TYPE_CHECKING:
    from refactor.protocol import RefactorRule

CASES = (
    (
        "dataframe-append-to-concat",
        "combined = frame.append(other)\n",
        "pd.concat([frame, other])",
    ),
    (
        "del-comprehension",
        "del_comprehension = 1\n",
        "Review Sourcery pattern for del-comprehension",
    ),
    (
        "dict-assign-update-to-union",
        "data.update(other)\n",
        "data |= other",
    ),
    (
        "dict-comprehension",
        "mapping = dict((key, value) for key, value in pairs)\n",
        "{key: value for key, value in pairs}",
    ),
    (
        "dont-import-test-modules",
        "dont_import_test_modules = 1\n",
        "Review Sourcery pattern for dont-import-test-modules",
    ),
    (
        "equality-identity",
        "if status is 'ready':\n    pass\n",
        "status == 'ready'",
    ),
    (
        "extract-duplicate-method",
        "class Example:\n    def extract_duplicate_method(self):\n        return 1\n",
        "Review method extraction pattern for extract-duplicate-method",
    ),
    (
        "extract-method",
        "class Example:\n    def extract_method(self):\n        return 1\n",
        "Review method extraction pattern for extract-method",
    ),
    (
        "flatten-nested-try",
        "try:\n    try:\n        risky()\n"
        "    except ValueError:\n        recover()\n"
        "except OSError:\n    reset()\n",
        "except OSError",
    ),
    (
        "flip-comparison",
        "if 10 > count:\n    pass\n",
        "count < 10",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_batch_03_detects_fixture(
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
def test_batch_03_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].safe_apply is False
