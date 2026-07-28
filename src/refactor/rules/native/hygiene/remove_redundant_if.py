"""Native rule for ``remove-redundant-if``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_false, is_true, single_small_stmt
from refactor.rules.native.stmt_base import IfRewriteRule


class RemoveRedundantIfRule(IfRewriteRule):
    rule_id = "remove-redundant-if"
    summary = "Remove redundant if"
    message = "Replace boolean-returning if with a direct return"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        body = node.body
        if not isinstance(body, cst.IndentedBlock):
            return None
        orelse_body = node.orelse.body
        if not isinstance(orelse_body, cst.IndentedBlock):
            return None
        value = cls.boolean_return_value(node, body, orelse_body)
        if value is None:
            return None
        return cst.SimpleStatementLine(body=[cst.Return(value=value)])

    @classmethod
    def boolean_return_value(
        cls,
        node: cst.If,
        body: cst.IndentedBlock,
        orelse_body: cst.IndentedBlock,
    ) -> cst.BaseExpression | None:
        then_value = cls.return_value(body)
        else_value = cls.return_value(orelse_body)
        return (
            None
            if then_value is None or else_value is None
            else (
                node.test
                if is_true(then_value) and is_false(else_value)
                else (
                    cst.UnaryOperation(operator=cst.Not(), expression=node.test)
                    if is_false(then_value) and is_true(else_value)
                    else None
                )
            )
        )

    @staticmethod
    def return_value(block: cst.IndentedBlock) -> cst.BaseExpression | None:
        stmt = single_small_stmt(block)
        return stmt.value if isinstance(stmt, cst.Return) and stmt.value is not None else None
