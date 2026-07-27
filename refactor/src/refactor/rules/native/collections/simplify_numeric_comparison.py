"""Native rule for ``simplify-numeric-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyNumericComparisonRule(PatternNativeRule):
    rule_id = "simplify-numeric-comparison"
    kind_value = "refactor"
    summary = "Simplify numeric comparison"
    needle = "simplify_numeric_comparison"
    replacement = "Review conditional pattern for simplify-numeric-comparison"
