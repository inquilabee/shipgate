"""Native rule for ``hoist-repeated-if-condition``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistRepeatedIfConditionRule(PatternNativeRule):
    rule_id = "hoist-repeated-if-condition"
    kind_value = "refactor"
    summary = "Hoist repeated if condition"
    needle = "hoist_repeated_if_condition"
    replacement = "Review conditional pattern for hoist-repeated-if-condition"
