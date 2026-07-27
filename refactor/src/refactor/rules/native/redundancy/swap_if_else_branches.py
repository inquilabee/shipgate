"""Native rule for ``swap-if-else-branches``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SwapIfElseBranchesRule(PatternNativeRule):
    rule_id = "swap-if-else-branches"
    kind_value = "refactor"
    summary = "Swap if else branches"
    needle = "swap_if_else_branches"
    replacement = "Review conditional pattern for swap-if-else-branches"
