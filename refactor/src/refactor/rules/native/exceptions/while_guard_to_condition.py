"""Native rule for ``while-guard-to-condition``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class WhileGuardToConditionRule(PatternNativeRule):
    rule_id = "while-guard-to-condition"
    kind_value = "refactor"
    summary = "While guard to condition"
    needle = "while_guard_to_condition"
    replacement = "Review conditional pattern for while-guard-to-condition"
