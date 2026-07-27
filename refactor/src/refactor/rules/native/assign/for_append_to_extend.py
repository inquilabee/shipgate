"""Native rule for ``for-append-to-extend``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import ForRewriteRule


class ForAppendToExtendRule(ForRewriteRule):
    rule_id = "for-append-to-extend"
    summary = "For append to extend"
    message = "Replace append loop with extend"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.For) or not isinstance(node.target, cst.Name):
            return None
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        stmt = single_small_stmt(node.body)
        if not isinstance(stmt, cst.Expr) or not isinstance(stmt.value, cst.Call):
            return None
        call = stmt.value
        if len(call.args) != 1 or call.args[0].keyword is not None:
            return None
        if not isinstance(call.func, cst.Attribute) or call.func.attr.value != "append":
            return None
        if not isinstance(call.args[0].value, cst.Name):
            return None
        if call.args[0].value.value != node.target.value:
            return None
        return cst.SimpleStatementLine(
            body=[
                cst.Expr(
                    value=cst.Call(
                        func=call.func.with_changes(attr=cst.Name("extend")),
                        args=[cst.Arg(value=node.iter)],
                    ),
                ),
            ],
        )
