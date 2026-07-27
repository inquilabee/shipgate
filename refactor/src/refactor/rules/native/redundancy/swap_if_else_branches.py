"""Native rule for ``swap-if-else-branches``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, swap_negated_if_exp


class SwapIfElseBranchesRule(IfExpRewriteRule):
    rule_id = "swap-if-else-branches"
    summary = "Swap if else branches"
    message = "Swap if-expression branches to remove a negated condition"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return swap_negated_if_exp(node)
