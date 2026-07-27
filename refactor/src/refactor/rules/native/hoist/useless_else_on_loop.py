"""Native rule for ``useless-else-on-loop``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UselessElseOnLoopRule(PatternNativeRule):
    rule_id = "useless-else-on-loop"
    kind_value = "refactor"
    summary = "Useless else on loop"
    needle = "useless_else_on_loop"
    replacement = "Review conditional pattern for useless-else-on-loop"
