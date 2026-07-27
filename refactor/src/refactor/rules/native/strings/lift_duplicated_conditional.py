"""Native rule for ``lift-duplicated-conditional``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class LiftDuplicatedConditionalRule(PatternNativeRule):
    rule_id = "lift-duplicated-conditional"
    kind_value = "refactor"
    summary = "Lift duplicated conditional"
    needle = "lift_duplicated_conditional"
    replacement = "Review conditional pattern for lift-duplicated-conditional"
