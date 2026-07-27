"""Native rule for ``hoist-statement-from-if``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.expr_base import IfRewriteRule

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class HoistStatementFromIfRule(IfRewriteRule):
    rule_id = "hoist-statement-from-if"
    summary = "Hoist statement from if"
    message = "Hoist a shared trailing statement out of both branches"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        orelse_body = node.orelse.body
        if not isinstance(orelse_body, cst.IndentedBlock):
            return None
        then_body = list(node.body.body)
        else_body = list(orelse_body.body)
        if not then_body or not else_body or not then_body[-1].deep_equals(else_body[-1]):
            return None
        common = cast("BodyStatement", then_body[-1])
        return [
            cast(
                "BodyStatement",
                node.with_changes(
                    body=node.body.with_changes(body=cls.with_pass_if_empty(then_body[:-1])),
                    orelse=node.orelse.with_changes(
                        body=orelse_body.with_changes(
                            body=cls.with_pass_if_empty(else_body[:-1]),
                        ),
                    ),
                ),
            ),
            common,
        ]

    @staticmethod
    def with_pass_if_empty(stmts: list[cst.BaseStatement]) -> list[cst.BaseStatement]:
        return stmts or [cst.SimpleStatementLine(body=[cst.Pass()])]
