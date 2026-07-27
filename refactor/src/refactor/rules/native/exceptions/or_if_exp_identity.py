"""Native rule for ``or-if-exp-identity``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, or_fallback_if_exp


class OrIfExpIdentityRule(IfExpRewriteRule):
    rule_id = "or-if-exp-identity"
    summary = "Or if exp identity"
    message = "Use or for an if-expression that returns its condition"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return or_fallback_if_exp(node)
