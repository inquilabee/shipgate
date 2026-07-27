"""Native rule for ``remove-redundant-condition``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfExpRewriteRule, same_branch_if_exp


class RemoveRedundantConditionRule(IfExpRewriteRule):
    rule_id = "remove-redundant-condition"
    summary = "Remove redundant condition"
    message = "Remove an if-expression whose branches are identical"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return same_branch_if_exp(node)
