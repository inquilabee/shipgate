"""Native rule for ``non-equal-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class NonEqualComparisonRule(PatternNativeRule):
    rule_id = "non-equal-comparison"
    kind_value = "refactor"
    summary = "Non equal comparison"
    needle = "non_equal_comparison"
    replacement = "Review comparison pattern for non-equal-comparison"
