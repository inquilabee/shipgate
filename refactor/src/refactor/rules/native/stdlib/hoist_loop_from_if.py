"""Native rule for ``hoist-loop-from-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistLoopFromIfRule(PatternNativeRule):
    rule_id = "hoist-loop-from-if"
    kind_value = "refactor"
    summary = "Hoist loop from if"
    needle = "hoist_loop_from_if"
    replacement = "Review conditional pattern for hoist-loop-from-if"
