"""Native rule for ``simplify-len-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyLenComparisonRule(PatternNativeRule):
    rule_id = "simplify-len-comparison"
    kind_value = "refactor"
    summary = "Simplify len comparison"
    needle = "simplify_len_comparison"
    replacement = "Review conditional pattern for simplify-len-comparison"
