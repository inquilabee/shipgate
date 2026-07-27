"""Native rule for ``split-or-ifs``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule


class SplitOrIfsRule(IfRewriteRule):
    rule_id = "split-or-ifs"
    summary = "Split or ifs"
    message = "Split an or condition into two if statements"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> list[cst.BaseStatement] | None:
        if not isinstance(node, cst.If) or node.orelse is not None:
            return None
        if not isinstance(node.test, cst.BooleanOperation) or not isinstance(
            node.test.operator,
            cst.Or,
        ):
            return None
        return [
            node.with_changes(test=node.test.left),
            node.with_changes(test=node.test.right),
        ]
