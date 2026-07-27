"""Native rule for ``set-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SetComprehensionRule(PatternNativeRule):
    rule_id = "set-comprehension"
    kind_value = "refactor"
    summary = "Set comprehension"
    needle = "set_comprehension"
    replacement = "Review collection pattern for set-comprehension"
