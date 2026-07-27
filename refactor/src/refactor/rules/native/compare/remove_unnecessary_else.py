"""Native rule for ``remove-unnecessary-else``."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import libcst as cst

from refactor.rules.native.expr_base import IfRewriteRule

if TYPE_CHECKING:
    from refactor.cst_util import BodyStatement


class RemoveUnnecessaryElseRule(IfRewriteRule):
    rule_id = "remove-unnecessary-else"
    summary = "Remove unnecessary else"
    message = "Remove else after a terminal if body"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[BodyStatement] | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        if not isinstance(node.body, cst.IndentedBlock) or not cls.ends_terminal(node.body):
            return None
        return [
            cast("BodyStatement", node.with_changes(orelse=None)),
            *[cast("BodyStatement", stmt) for stmt in node.orelse.body.body],
        ]

    @staticmethod
    def ends_terminal(block: cst.IndentedBlock) -> bool:
        if not block.body:
            return False
        last = block.body[-1]
        if not isinstance(last, cst.SimpleStatementLine) or len(last.body) != 1:
            return False
        return isinstance(last.body[0], cst.Return | cst.Raise | cst.Break | cst.Continue)
