"""Native rule for ``simplify-numeric-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class SimplifyNumericComparisonRule(ComparisonRewriteRule):
    rule_id = "simplify-numeric-comparison"
    summary = "Simplify numeric comparison"
    message = "Compare numeric operands directly instead of comparing their difference to zero"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        if not isinstance(node.left, cst.BinaryOperation) or not isinstance(
            node.left.operator,
            cst.Subtract,
        ):
            return None
        target = node.comparisons[0]
        if not cls.is_zero(target.comparator):
            return None
        return cst.Comparison(
            left=node.left.left,
            comparisons=[
                cst.ComparisonTarget(
                    operator=target.operator,
                    comparator=node.left.right,
                ),
            ],
        )

    @staticmethod
    def is_zero(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer) and node.value == "0"
