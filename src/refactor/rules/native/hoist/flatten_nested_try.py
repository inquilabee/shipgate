"""Native rule for ``flatten-nested-try``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import TryRewriteRule


class FlattenNestedTryRule(TryRewriteRule):
    rule_id = "flatten-nested-try"
    summary = "Flatten nested try"
    message = "Flatten nested try statements"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        if not isinstance(node, cst.Try):
            return None
        if node.orelse is not None or node.finalbody is not None:
            return None
        if not isinstance(node.body, cst.IndentedBlock) or len(node.body.body) != 1:
            return None
        inner = node.body.body[0]
        if not isinstance(inner, cst.Try):
            return None
        if inner.orelse is not None or inner.finalbody is not None:
            return None
        return inner.with_changes(handlers=[*inner.handlers, *node.handlers])
