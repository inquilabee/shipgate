"""Native rule for ``swap-nested-ifs``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SwapNestedIfsRule(PatternNativeRule):
    rule_id = "swap-nested-ifs"
    kind_value = "refactor"
    summary = "Swap nested ifs"
    needle = "swap_nested_ifs"
    replacement = "Review conditional pattern for swap-nested-ifs"
