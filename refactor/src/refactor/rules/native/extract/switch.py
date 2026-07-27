"""Native rule for ``switch``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SwitchRule(PatternNativeRule):
    rule_id = "switch"
    kind_value = "refactor"
    summary = "Switch"
    needle = "switch"
    replacement = "Review conditional pattern for switch"
