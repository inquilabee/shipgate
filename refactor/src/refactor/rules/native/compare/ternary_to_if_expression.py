"""Native rule for ``ternary-to-if-expression``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class TernaryToIfExpressionRule(PatternNativeRule):
    rule_id = "ternary-to-if-expression"
    kind_value = "refactor"
    summary = "Ternary to if expression"
    needle = "ternary_to_if_expression"
    replacement = "Review conditional pattern for ternary-to-if-expression"
