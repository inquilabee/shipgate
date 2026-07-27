"""Native rule for ``merge-else-if-into-elif``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfRewriteRule


class MergeElseIfIntoElifRule(IfRewriteRule):
    rule_id = "merge-else-if-into-elif"
    summary = "Merge else if into elif"
    message = "Use elif instead of else containing a single if"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.Else):
            return None
        body = node.orelse.body.body
        if len(body) != 1 or not isinstance(body[0], cst.If):
            return None
        return node.with_changes(orelse=body[0])
