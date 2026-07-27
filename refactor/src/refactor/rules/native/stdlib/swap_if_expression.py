"""Native rule for ``swap-if-expression``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, swap_negated_if_exp


class SwapIfExpressionRule(IfExpRewriteRule):
    rule_id = "swap-if-expression"
    summary = "Swap if expression"
    message = "Swap if-expression branches to remove a negated condition"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return swap_negated_if_exp(node)
