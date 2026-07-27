"""Native rule for ``or-if-exp-identity``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule


class OrIfExpIdentityRule(IfExpRewriteRule):
    rule_id = "or-if-exp-identity"
    summary = "Or if exp identity"
    message = "Use or for an if-expression that returns its condition"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.IfExp):
            return None
        if not node.body.deep_equals(node.test):
            return None
        return cst.BooleanOperation(
            left=node.test,
            operator=cst.Or(),
            right=node.orelse,
        )
