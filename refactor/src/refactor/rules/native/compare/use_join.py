"""Native rule for ``use-join``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseJoinRule(PatternNativeRule):
    rule_id = "use-join"
    kind_value = "refactor"
    summary = "Use join"
    needle = "use_join"
    replacement = "Review string pattern for use-join"
