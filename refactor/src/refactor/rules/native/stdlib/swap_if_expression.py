"""Native rule for ``swap-if-expression``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SwapIfExpressionRule(PatternNativeRule):
    rule_id = "swap-if-expression"
    kind_value = "refactor"
    summary = "Swap if expression"
    needle = "swap_if_expression"
    replacement = "Review conditional pattern for swap-if-expression"
