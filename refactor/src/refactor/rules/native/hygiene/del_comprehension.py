"""Native rule for ``del-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, name_target_for_body_stmt


class DelComprehensionRule(ForRewriteRule):
    rule_id = "del-comprehension"
    summary = "Del comprehension"
    message = "Use pop when deleting keys in a loop"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        loop = name_target_for_body_stmt(node)
        if loop is None:
            return None
        loop_target, iter_expr, stmt = loop
        if not isinstance(stmt, cst.Del):
            return None
        target = stmt.target
        if not isinstance(target, cst.Subscript) or len(target.slice) != 1:
            return None
        if not isinstance(target.slice[0].slice, cst.Index):
            return None
        index = target.slice[0].slice.value
        if not isinstance(index, cst.Name) or index.value != loop_target.value:
            return None
        return cst.For(
            target=loop_target,
            iter=iter_expr,
            body=cst.IndentedBlock(
                body=[
                    cst.SimpleStatementLine(
                        body=[
                            cst.Expr(
                                value=cst.Call(
                                    func=cst.Attribute(value=target.value, attr=cst.Name("pop")),
                                    args=[
                                        cst.Arg(value=index),
                                        cst.Arg(value=cst.Name("None")),
                                    ],
                                ),
                            ),
                        ],
                    ),
                ],
            ),
        )
