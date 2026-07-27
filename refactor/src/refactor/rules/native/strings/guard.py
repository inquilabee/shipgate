"""Native rule for ``guard``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, negated_expr, single_terminal_stmt

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class GuardRule(IfRewriteRule):
    rule_id = "guard"
    summary = "Guard"
    message = "Use a guard clause for the terminal else branch"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        if not isinstance(node.body, cst.IndentedBlock):
            return None
        if not isinstance(node.orelse.body, cst.IndentedBlock):
            return None
        if single_terminal_stmt(node.orelse.body) is None:
            return None
        return [
            cast(
                "BodyStatement",
                node.with_changes(
                    test=negated_expr(node.test),
                    body=node.orelse.body,
                    orelse=None,
                ),
            ),
            *[cast("BodyStatement", stmt) for stmt in node.body.body],
        ]
