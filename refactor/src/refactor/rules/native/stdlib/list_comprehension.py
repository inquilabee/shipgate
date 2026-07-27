"""Native rule for ``list-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ListComprehensionRule(PatternNativeRule):
    rule_id = "list-comprehension"
    kind_value = "refactor"
    summary = "List comprehension"
    needle = "list_comprehension"
    replacement = "Review collection pattern for list-comprehension"
