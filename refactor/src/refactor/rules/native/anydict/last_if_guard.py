"""Native rule for ``last-if-guard``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class LastIfGuardRule(PatternNativeRule):
    rule_id = "last-if-guard"
    kind_value = "refactor"
    summary = "Last if guard"
    needle = "last_if_guard"
    replacement = "Review conditional pattern for last-if-guard"
