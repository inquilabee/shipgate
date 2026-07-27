"""Native rule for ``remove-pass-elif``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import single_small_stmt
from refactor.rules.native.stmt_base import IfRewriteRule


class RemovePassElifRule(IfRewriteRule):
    rule_id = "remove-pass-elif"
    summary = "Remove pass elif"
    message = "Remove an elif branch that only passes"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.If) or not isinstance(node.orelse, cst.If):
            return None
        if not isinstance(node.orelse.body, cst.IndentedBlock):
            return None
        if not isinstance(single_small_stmt(node.orelse.body), cst.Pass):
            return None
        return node.with_changes(orelse=node.orelse.orelse)
