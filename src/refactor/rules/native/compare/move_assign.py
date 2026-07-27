"""Native rule for ``move-assign``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import (
    IfRewriteRule,
    if_else_blocks,
    single_assign_block,
)


class MoveAssignRule(IfRewriteRule):
    rule_id = "move-assign"
    summary = "Move assign"
    message = "Move duplicated assignment target outside the conditional"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        blocks = if_else_blocks(node)
        if blocks is None or not isinstance(node, cst.If):
            return None
        left_assign = single_assign_block(blocks[0])
        right_assign = single_assign_block(blocks[1])
        if left_assign is None or right_assign is None:
            return None
        left_target, left_value = left_assign
        right_target, right_value = right_assign
        if not left_target.deep_equals(right_target):
            return None
        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=[cst.AssignTarget(target=left_target)],
                    value=cst.IfExp(test=node.test, body=left_value, orelse=right_value),
                ),
            ],
        )
