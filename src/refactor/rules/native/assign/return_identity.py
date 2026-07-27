"""Native rule for ``return-identity``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, same_branch_if_exp


class ReturnIdentityRule(IfExpRewriteRule):
    rule_id = "return-identity"
    summary = "Return identity"
    message = "Return the shared branch directly from an if-expression"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return same_branch_if_exp(node)
