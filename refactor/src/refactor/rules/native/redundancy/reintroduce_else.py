"""Native rule for ``reintroduce-else``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReintroduceElseRule(PatternNativeRule):
    rule_id = "reintroduce-else"
    kind_value = "refactor"
    summary = "Reintroduce else"
    needle = "reintroduce_else"
    replacement = "Review conditional pattern for reintroduce-else"
