"""Native rule for ``flip-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class FlipComparisonRule(ComparisonRewriteRule):
    rule_id = "flip-comparison"
    summary = "Flip comparison"
    message = "Put the variable side first in a simple comparison"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        target = node.comparisons[0]
        if not cls.should_flip(node.left, target.comparator):
            return None
        flipped_operator = cls.flipped_operator(target.operator)
        if flipped_operator is None:
            return None
        return cst.Comparison(
            left=target.comparator,
            comparisons=[
                cst.ComparisonTarget(
                    operator=flipped_operator,
                    comparator=node.left,
                ),
            ],
        )

    @staticmethod
    def should_flip(left: cst.BaseExpression, right: cst.BaseExpression) -> bool:
        return isinstance(left, cst.Integer | cst.Float | cst.SimpleString) and isinstance(
            right,
            cst.Name | cst.Attribute | cst.Subscript,
        )

    @staticmethod
    def flipped_operator(operator: cst.BaseCompOp) -> cst.BaseCompOp | None:
        flipped_by_type: dict[type[cst.BaseCompOp], cst.BaseCompOp] = {
            cst.LessThan: cst.GreaterThan(),
            cst.LessThanEqual: cst.GreaterThanEqual(),
            cst.GreaterThan: cst.LessThan(),
            cst.GreaterThanEqual: cst.LessThanEqual(),
            cst.NotEqual: cst.NotEqual(),
            cst.Equal: cst.Equal(),
        }
        return flipped_by_type.get(type(operator))
