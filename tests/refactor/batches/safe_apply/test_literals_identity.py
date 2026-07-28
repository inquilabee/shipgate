from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

SAFE_APPLY_RULE_IDS = (
    "dict-literal",
    "tuple-literal",
    "aug-assign",
    "bin-op-identity",
    "remove-redundant-pass",
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(
    ("rule_id", "before", "after"),
    [
        ("dict-literal", "x = dict()\n", "x = {}\n"),
        ("tuple-literal", "x = tuple()\n", "x = ()\n"),
        ("aug-assign", "x = x + 1\n", "x += 1\n"),
        ("bin-op-identity", "y = x + 0\n", "y = x\n"),
        (
            "remove-redundant-pass",
            "def f():\n    x = 1\n    pass\n",
            "def f():\n    x = 1\n",
        ),
    ],
)
def test_safe_apply_round_trip(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    before: str,
    after: str,
) -> None:
    rule = rules_by_id[rule_id]
    assert rule.apply_mode is ApplyMode.AUTO
    hits = rule.detect(before, "sample.py")
    assert len(hits) >= 1
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert not rule.detect(rewritten or "", "sample.py")


def test_bin_op_identity_skips_multi_target_assign(
    rules_by_id: dict[str, RefactorRule],
) -> None:
    rule = rules_by_id["bin-op-identity"]
    source = "a = b = x + 0\ny = z + 0\n"
    hits = rule.detect(source, "sample.py")
    assert len(hits) == 1
    rewritten = rule.apply(source, hits)
    assert rewritten == "a = b = x + 0\ny = z\n"
    assert not rule.detect(rewritten or "", "sample.py")


@pytest.mark.parametrize(
    ("rule_id", "before", "after"),
    [
        (
            "dict-literal",
            "a = dict()\nb = dict()\n",
            "a = {}\nb = {}\n",
        ),
        (
            "tuple-literal",
            "a = tuple()\nb = tuple()\n",
            "a = ()\nb = ()\n",
        ),
        (
            "aug-assign",
            "x = x + 1\ny = y - 2\n",
            "x += 1\ny -= 2\n",
        ),
        (
            "bin-op-identity",
            "a = x + 0\nb = y * 1\n",
            "a = x\nb = y\n",
        ),
        (
            "remove-redundant-pass",
            "def f():\n    x = 1\n    pass\n\ndef g():\n    y = 2\n    pass\n",
            "def f():\n    x = 1\n\ndef g():\n    y = 2\n",
        ),
    ],
)
def test_safe_apply_fixes_all_occurrences(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    before: str,
    after: str,
) -> None:
    rule = rules_by_id[rule_id]
    hits = rule.detect(before, "sample.py")
    assert len(hits) >= 2
    rewritten = rule.apply(before, hits)
    assert rewritten == after
    assert not rule.detect(rewritten or "", "sample.py")
