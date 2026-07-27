"""Native rule for ``skip-sorted-list-construction``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SkipSortedListConstructionRule(PatternNativeRule):
    rule_id = "skip-sorted-list-construction"
    kind_value = "refactor"
    summary = "Skip sorted list construction"
    needle = "skip_sorted_list_construction"
    replacement = "Review collection pattern for skip-sorted-list-construction"
