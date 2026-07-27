"""Native rule for ``simplify-constant-sum``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifyConstantSumRule(PatternNativeRule):
    rule_id = "simplify-constant-sum"
    kind_value = "refactor"
    summary = "Simplify constant sum"
    needle = "simplify_constant_sum"
    replacement = "Review conditional pattern for simplify-constant-sum"
