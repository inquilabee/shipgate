"""Native rule for ``swap-variable``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SwapVariableRule(PatternNativeRule):
    rule_id = "swap-variable"
    kind_value = "refactor"
    summary = "Swap variable"
    needle = "swap_variable"
    replacement = "Review Sourcery pattern for swap-variable"
