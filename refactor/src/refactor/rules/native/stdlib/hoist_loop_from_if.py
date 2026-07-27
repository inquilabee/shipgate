"""Native rule for ``hoist-loop-from-if``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule


class HoistLoopFromIfRule(IfRewriteRule):
    rule_id = "hoist-loop-from-if"
    summary = "Hoist loop from if"
    message = "Hoist a loop out of an if body"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or node.orelse is not None:
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
            return None
        loop = node.body.body[0]
        if not isinstance(loop, cst.For | cst.While):
            return None
        if not isinstance(loop.body, cst.IndentedBlock):
            return None
        return loop.with_changes(
            body=loop.body.with_changes(
                body=[cst.If(test=node.test, body=loop.body)],
            ),
        )
