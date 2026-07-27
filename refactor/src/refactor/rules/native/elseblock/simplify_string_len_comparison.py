"""Native rule for ``simplify-string-len-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyStringLenComparisonRule(PatternNativeRule):
    rule_id = "simplify-string-len-comparison"
    kind_value = "refactor"
    summary = "Simplify string len comparison"
    needle = "simplify_string_len_comparison"
    replacement = "Review string pattern for simplify-string-len-comparison"
