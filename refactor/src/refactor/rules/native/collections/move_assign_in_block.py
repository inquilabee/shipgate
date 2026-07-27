"""Native rule for ``move-assign-in-block``."""

from __future__ import annotations

from refactor.rules.native.compare.move_assign import MoveAssignRule


class MoveAssignInBlockRule(MoveAssignRule):
    rule_id = "move-assign-in-block"
    summary = "Move assign in block"
    message = "Move duplicated assignment target outside the block conditional"
