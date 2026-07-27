"""Native rule for ``flip-comparison``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class FlipComparisonRule(PatternNativeRule):
    rule_id = "flip-comparison"
    kind_value = "refactor"
    summary = "Flip comparison"
    needle = "flip_comparison"
    replacement = "Review comparison pattern for flip-comparison"
