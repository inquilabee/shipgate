"""Native rule for ``chain-compares``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BooleanOpRewriteRule


class ChainComparesRule(BooleanOpRewriteRule):
    rule_id = "chain-compares"
    summary = "Chain compares"
    message = "Chain adjacent comparisons sharing the middle operand"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BooleanOperation) or not isinstance(node.operator, cst.And):
            return None
        if not isinstance(node.left, cst.Comparison) or not isinstance(node.right, cst.Comparison):
            return None
        if len(node.left.comparisons) != 1 or len(node.right.comparisons) != 1:
            return None
        left_target = node.left.comparisons[0]
        if not left_target.comparator.deep_equals(node.right.left):
            return None
        return cst.Comparison(
            left=node.left.left,
            comparisons=[left_target, node.right.comparisons[0]],
        )
