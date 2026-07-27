"""Native rule for ``hoist-loop-from-if``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, if_without_else_single_body


class HoistLoopFromIfRule(IfRewriteRule):
    rule_id = "hoist-loop-from-if"
    summary = "Hoist loop from if"
    message = "Hoist a loop out of an if body"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        match = if_without_else_single_body(node)
        if match is None:
            return None
        if_stmt, loop = match
        if not isinstance(loop, cst.For | cst.While):
            return None
        if not isinstance(loop.body, cst.IndentedBlock):
            return None
        return loop.with_changes(
            body=loop.body.with_changes(
                body=[cst.If(test=if_stmt.test, body=loop.body)],
            ),
        )
