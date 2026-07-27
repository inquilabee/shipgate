"""Native rule for ``guard``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class GuardRule(PatternNativeRule):
    rule_id = "guard"
    kind_value = "refactor"
    summary = "Guard"
    needle = "guard"
    replacement = "Review conditional pattern for guard"
