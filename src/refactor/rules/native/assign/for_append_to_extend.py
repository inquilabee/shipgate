"""Native rule for ``for-append-to-extend``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import ForRewriteRule, name_target_for_body_stmt


class ForAppendToExtendRule(ForRewriteRule):
    rule_id = "for-append-to-extend"
    summary = "For append to extend"
    message = "Replace append loop with extend"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        loop = name_target_for_body_stmt(node)
        if loop is None:
            return None
        target, iter_expr, stmt = loop
        append_call = cls.append_name_call(stmt, target.value)
        if append_call is None:
            return None
        return cst.SimpleStatementLine(
            body=[
                cst.Expr(
                    value=cst.Call(
                        func=append_call.with_changes(attr=cst.Name("extend")),
                        args=[cst.Arg(value=iter_expr)],
                    ),
                ),
            ],
        )

    @staticmethod
    def append_name_call(stmt: cst.BaseSmallStatement, target_name: str) -> cst.Attribute | None:
        if not isinstance(stmt, cst.Expr) or not isinstance(stmt.value, cst.Call):
            return None
        call = stmt.value
        if len(call.args) != 1 or call.args[0].keyword is not None:
            return None
        if not isinstance(call.func, cst.Attribute) or call.func.attr.value != "append":
            return None
        if not isinstance(call.args[0].value, cst.Name):
            return None
        if call.args[0].value.value != target_name:
            return None
        return call.func
