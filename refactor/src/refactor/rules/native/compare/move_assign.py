"""Native rule for ``move-assign``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MoveAssignRule(PatternNativeRule):
    rule_id = "move-assign"
    kind_value = "refactor"
    summary = "Move assign"
    needle = "move_assign"
    replacement = "Review Sourcery pattern for move-assign"
