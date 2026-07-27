"""Native rule for ``move-assign-in-block``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MoveAssignInBlockRule(PatternNativeRule):
    rule_id = "move-assign-in-block"
    kind_value = "refactor"
    summary = "Move assign in block"
    needle = "move_assign_in_block"
    replacement = "Review Sourcery pattern for move-assign-in-block"
