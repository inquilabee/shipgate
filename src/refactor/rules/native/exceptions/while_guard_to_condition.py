"""Native rule for ``while-guard-to-condition``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import not_operation
from refactor.cst_util import is_true, single_small_stmt
from refactor.rules.native.stmt_base import WhileRewriteRule


class WhileGuardToConditionRule(WhileRewriteRule):
    rule_id = "while-guard-to-condition"
    summary = "While guard to condition"
    message = "Move a leading while guard into the loop condition"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.While) or not is_true(node.test):
            return None
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        guard_test = cls.break_guard_test(node.body)
        if guard_test is None:
            return None
        return node.with_changes(
            test=guard_test,
            body=node.body.with_changes(body=node.body.body[1:]),
        )

    @staticmethod
    def break_guard_test(body: cst.IndentedBlock) -> cst.BaseExpression | None:
        if len(body.body) < 2:
            return None
        guard = body.body[0]
        if not isinstance(guard, cst.If) or guard.orelse is not None:
            return None
        not_test = not_operation(guard.test)
        if not_test is None:
            return None
        if not isinstance(guard.body, cst.IndentedBlock):
            return None
        if not isinstance(single_small_stmt(guard.body), cst.Break):
            return None
        return not_test.expression
