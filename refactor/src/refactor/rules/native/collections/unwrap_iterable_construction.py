"""Native rule for ``unwrap-iterable-construction``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UnwrapIterableConstructionRule(PatternNativeRule):
    rule_id = "unwrap-iterable-construction"
    kind_value = "refactor"
    summary = "Unwrap iterable construction"
    needle = "unwrap_iterable_construction"
    replacement = "Review collection pattern for unwrap-iterable-construction"
