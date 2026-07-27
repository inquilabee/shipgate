"""Native rule for ``use-or-for-fallback``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, or_fallback_if_exp


class UseOrForFallbackRule(IfExpRewriteRule):
    rule_id = "use-or-for-fallback"
    summary = "Use or for fallback"
    message = "Use or for a value fallback"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return or_fallback_if_exp(node)
