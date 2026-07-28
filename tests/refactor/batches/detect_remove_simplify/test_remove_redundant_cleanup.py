from __future__ import annotations

import pytest

from refactor.protocol import ApplyMode, RefactorRule
from refactor.registry import RULES

CASES = (
    (
        "remove-duplicate-set-key",
        'items = {"a", "b", "a"}\n',
        '{"a", "b"}',
    ),
    (
        "remove-empty-nested-block",
        "if ready:\n    if unused:\n        pass\n",
        "",
    ),
    (
        "remove-none-from-default-get",
        "value = data.get(key, None)\n",
        "data.get(key)",
    ),
    (
        "remove-pass-body",
        "if ready:\n    pass\n",
        "",
    ),
    (
        "remove-pass-elif",
        "if ready:\n    run()\nelif stale:\n    pass\nelse:\n    recover()\n",
        "else:\n    recover()",
    ),
    (
        "remove-redundant-boolean",
        "if bool(ready):\n    pass\n",
        "ready",
    ),
    (
        "remove-redundant-condition",
        "result = value if condition else value\n",
        "value",
    ),
    (
        "remove-redundant-constructor-in-dict-union",
        "data = dict(left) | dict(right)\n",
        "left | right",
    ),
    (
        "remove-redundant-continue",
        "for item in items:\n    process(item)\n    continue\n",
        "process(item)",
    ),
    (
        "remove-redundant-except-handler",
        "try:\n    risky()\nexcept ValueError:\n    raise\n",
        "risky()",
    ),
)


@pytest.fixture
def rules_by_id() -> dict[str, RefactorRule]:
    return {rule.rule_id: rule for rule in RULES}


@pytest.mark.parametrize(("rule_id", "source", "expected"), CASES)
def test_remove_redundant_cleanup_detects_fixture(
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
def test_remove_redundant_cleanup_safe_apply_false(
    rules_by_id: dict[str, RefactorRule],
    rule_id: str,
    source: str,
    expected: str,
) -> None:
    _ = source, expected
    assert rules_by_id[rule_id].apply_mode is not ApplyMode.AUTO
