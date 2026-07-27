"""Native rule for ``lift-return-into-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class LiftReturnIntoIfRule(PatternNativeRule):
    rule_id = "lift-return-into-if"
    kind_value = "refactor"
    summary = "Lift return into if"
    needle = "lift_return_into_if"
    replacement = "Review conditional pattern for lift-return-into-if"
