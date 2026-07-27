"""Native rule for ``while-to-for``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import WhileRewriteRule


class WhileToForRule(WhileRewriteRule):
    rule_id = "while-to-for"
    summary = "While to for"
    message = "Use a for loop over range for index iteration"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.While) or not isinstance(node.test, cst.Comparison):
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) < 2:
            return None
        index_name, length_arg = cls.len_bound(node.test)
        if index_name is None or length_arg is None:
            return None
        increment = cls.trailing_increment(node.body.body[-1], index_name)
        if increment is None:
            return None
        return cst.For(
            target=cst.Name(index_name),
            iter=cst.Call(
                func=cst.Name("range"),
                args=[
                    cst.Arg(
                        value=cst.Call(
                            func=cst.Name("len"),
                            args=[cst.Arg(value=length_arg)],
                        ),
                    ),
                ],
            ),
            body=node.body.with_changes(body=node.body.body[:-1]),
        )

    @staticmethod
    def len_bound(node: cst.Comparison) -> tuple[str | None, cst.BaseExpression | None]:
        if len(node.comparisons) != 1 or not isinstance(node.left, cst.Name):
            return None, None
        target = node.comparisons[0]
        if not isinstance(target.operator, cst.LessThan):
            return None, None
        if not isinstance(target.comparator, cst.Call):
            return None, None
        call = target.comparator
        if not isinstance(call.func, cst.Name) or call.func.value != "len":
            return None, None
        if len(call.args) != 1 or call.args[0].keyword is not None:
            return None, None
        return node.left.value, call.args[0].value

    @staticmethod
    def trailing_increment(stmt: cst.BaseStatement, index_name: str) -> cst.AugAssign | None:
        if not isinstance(stmt, cst.SimpleStatementLine) or len(stmt.body) != 1:
            return None
        small_stmt = stmt.body[0]
        if not isinstance(small_stmt, cst.AugAssign):
            return None
        if not isinstance(small_stmt.target, cst.Name) or small_stmt.target.value != index_name:
            return None
        if not isinstance(small_stmt.operator, cst.AddAssign):
            return None
        if not isinstance(small_stmt.value, cst.Integer) or small_stmt.value.value != "1":
            return None
        return small_stmt
