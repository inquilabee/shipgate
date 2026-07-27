"""Native rule for ``del-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class DelComprehensionRule(PatternNativeRule):
    rule_id = "del-comprehension"
    kind_value = "refactor"
    summary = "Del comprehension"
    needle = "del_comprehension"
    replacement = "Review Sourcery pattern for del-comprehension"
