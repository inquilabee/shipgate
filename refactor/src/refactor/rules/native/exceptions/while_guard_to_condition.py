"""Native rule for ``while-guard-to-condition``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_true, single_small_stmt
from refactor.rules.native.expr_base import WhileRewriteRule


class WhileGuardToConditionRule(WhileRewriteRule):
    rule_id = "while-guard-to-condition"
    summary = "While guard to condition"
    message = "Move a leading while guard into the loop condition"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.While) or not is_true(node.test):
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) < 2:
            return None
        guard = node.body.body[0]
        if not isinstance(guard, cst.If) or guard.orelse is not None:
            return None
        if not isinstance(guard.test, cst.UnaryOperation) or not isinstance(
            guard.test.operator,
            cst.Not,
        ):
            return None
        if not isinstance(guard.body, cst.IndentedBlock):
            return None
        if not isinstance(single_small_stmt(guard.body), cst.Break):
            return None
        return node.with_changes(
            test=guard.test.expression,
            body=node.body.with_changes(body=node.body.body[1:]),
        )
