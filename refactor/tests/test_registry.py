from __future__ import annotations

from refactor.protocol import RuleKind
from refactor.registry import RULES


def test_registry_has_at_least_twenty_native_rules() -> None:
    native_rules = [rule for rule in RULES if rule.rule_id != "list-literal"]
    assert len(native_rules) >= 20
    assert all(rule.kind in {RuleKind.REFACTOR, RuleKind.SUGGESTION} for rule in native_rules)
