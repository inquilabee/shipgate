"""Native rule for ``remove-redundant-condition``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule


class RemoveRedundantConditionRule(IfExpRewriteRule):
    rule_id = "remove-redundant-condition"
    summary = "Remove redundant condition"
    message = "Remove an if-expression whose branches are identical"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return (
            node.body
            if isinstance(node, cst.IfExp) and node.body.deep_equals(node.orelse)
            else None
        )
