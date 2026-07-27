"""Native rule for ``remove-redundant-path-exists``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import IfRewriteRule


class RemoveRedundantPathExistsRule(IfRewriteRule):
    rule_id = "remove-redundant-path-exists"
    summary = "Remove redundant path exists"
    message = "Use missing_ok instead of checking path existence"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If):
            return None
        exists_call = cls.path_exists_test(node)
        if exists_call is None:
            return None
        unlink_call = cls.unlink_on_same_target(node, exists_call)
        if unlink_call is None:
            return None
        return cls.unlink_with_missing_ok(unlink_call)

    @staticmethod
    def path_exists_test(node: cst.If) -> cst.Call | None:
        if node.orelse is not None:
            return None
        if not isinstance(node.test, cst.Call) or node.test.args:
            return None
        if not isinstance(node.test.func, cst.Attribute) or node.test.func.attr.value != "exists":
            return None
        return node.test

    @staticmethod
    def unlink_on_same_target(node: cst.If, exists_call: cst.Call) -> cst.Call | None:
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        stmt = single_small_stmt(node.body)
        if not isinstance(stmt, cst.Expr) or not isinstance(stmt.value, cst.Call):
            return None
        call = stmt.value
        if not isinstance(call.func, cst.Attribute) or call.func.attr.value != "unlink":
            return None
        if not isinstance(exists_call.func, cst.Attribute):
            return None
        if not call.func.value.deep_equals(exists_call.func.value) or call.args:
            return None
        return call

    @staticmethod
    def unlink_with_missing_ok(call: cst.Call) -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=[
                cst.Expr(
                    value=call.with_changes(
                        args=[
                            cst.Arg(
                                keyword=cst.Name("missing_ok"),
                                value=cst.Name("True"),
                                equal=cst.AssignEqual(
                                    whitespace_before=cst.SimpleWhitespace(""),
                                    whitespace_after=cst.SimpleWhitespace(""),
                                ),
                            ),
                        ],
                    ),
                ),
            ],
        )
