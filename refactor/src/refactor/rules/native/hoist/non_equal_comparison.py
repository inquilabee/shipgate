"""Native rule for ``non-equal-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import UnaryOpRewriteRule


class NonEqualComparisonRule(UnaryOpRewriteRule):
    rule_id = "non-equal-comparison"
    summary = "Non equal comparison"
    message = "Use a direct equality operator instead of negating a comparison"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.UnaryOperation) or not isinstance(node.operator, cst.Not):
            return None
        if not isinstance(node.expression, cst.Comparison):
            return None
        comparison = node.expression
        if len(comparison.comparisons) != 1:
            return None
        target = comparison.comparisons[0]
        if isinstance(target.operator, cst.Equal):
            operator: cst.BaseCompOp = cst.NotEqual()
        elif isinstance(target.operator, cst.NotEqual):
            operator = cst.Equal()
        else:
            return None
        return cst.Comparison(
            left=comparison.left,
            comparisons=[
                cst.ComparisonTarget(
                    operator=operator,
                    comparator=target.comparator,
                ),
            ],
        )
