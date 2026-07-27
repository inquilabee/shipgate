"""Native rule for ``ternary-to-if-expression``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.expr_base import IfRewriteRule


class TernaryToIfExpressionRule(IfRewriteRule):
    rule_id = "ternary-to-if-expression"
    summary = "Ternary to if expression"
    message = "Replace branch assignments with a conditional expression"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        then_assign = cls.single_assign(node.body)
        orelse_body = node.orelse.body
        if not isinstance(orelse_body, cst.IndentedBlock):
            return None
        else_assign = cls.single_assign(orelse_body)
        if then_assign is None or else_assign is None:
            return None
        if len(then_assign.targets) != 1 or len(else_assign.targets) != 1:
            return None
        if not then_assign.targets[0].target.deep_equals(else_assign.targets[0].target):
            return None
        return cst.SimpleStatementLine(
            body=[
                then_assign.with_changes(
                    value=cst.IfExp(
                        test=node.test,
                        body=then_assign.value,
                        orelse=else_assign.value,
                    ),
                ),
            ],
        )

    @staticmethod
    def single_assign(block: cst.IndentedBlock) -> cst.Assign | None:
        stmt = single_small_stmt(block)
        return stmt if isinstance(stmt, cst.Assign) else None
