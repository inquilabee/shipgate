"""Native rule for ``remove-unnecessary-else``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveUnnecessaryElseRule(PatternNativeRule):
    rule_id = "remove-unnecessary-else"
    kind_value = "refactor"
    summary = "Remove unnecessary else"
    needle = "remove_unnecessary_else"
    replacement = "Review conditional pattern for remove-unnecessary-else"
