"""Native rule for ``non-equal-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import inverted_equal_operator, not_operation
from refactor.rules.native.expr_base import UnaryOpRewriteRule


class NonEqualComparisonRule(UnaryOpRewriteRule):
    rule_id = "non-equal-comparison"
    summary = "Non equal comparison"
    message = "Use a direct equality operator instead of negating a comparison"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        not_node = not_operation(node)
        if not_node is None or not isinstance(not_node.expression, cst.Comparison):
            return None
        comparison = not_node.expression
        if len(comparison.comparisons) != 1:
            return None
        target = comparison.comparisons[0]
        operator = inverted_equal_operator(target.operator)
        if operator is None:
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
