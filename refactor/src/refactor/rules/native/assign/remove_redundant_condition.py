"""Native rule for ``remove-redundant-condition``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantConditionRule(PatternNativeRule):
    rule_id = "remove-redundant-condition"
    kind_value = "refactor"
    summary = "Remove redundant condition"
    needle = "remove_redundant_condition"
    replacement = "Review conditional pattern for remove-redundant-condition"
