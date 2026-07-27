"""Native rule for ``simplify-string-len-comparison``."""

from __future__ import annotations

from refactor.rules.native.compare.simplify_len_comparison import SimplifyLenComparisonRule


class SimplifyStringLenComparisonRule(SimplifyLenComparisonRule):
    rule_id = "simplify-string-len-comparison"
    summary = "Simplify string len comparison"
    message = "Use string truthiness instead of comparing len() to zero"
