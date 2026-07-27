"""Native rule for ``hoist-if-from-if``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class HoistIfFromIfRule(PatternNativeRule):
    rule_id = "hoist-if-from-if"
    kind_value = "refactor"
    summary = "Hoist if from if"
    needle = "hoist_if_from_if"
    replacement = "Review conditional pattern for hoist-if-from-if"
