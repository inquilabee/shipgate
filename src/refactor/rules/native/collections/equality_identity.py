"""Native rule for ``equality-identity``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class EqualityIdentityRule(ComparisonRewriteRule):
    rule_id = "equality-identity"
    summary = "Equality identity"
    message = "Use equality for non-singleton value comparisons"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        target = node.comparisons[0]
        if not cls.is_value_literal(target.comparator):
            return None
        if not isinstance(target.operator, cst.Is | cst.IsNot):
            return None
        operator: cst.BaseCompOp = (
            cst.Equal() if isinstance(target.operator, cst.Is) else cst.NotEqual()
        )
        return cst.Comparison(
            left=node.left,
            comparisons=[
                cst.ComparisonTarget(
                    operator=operator,
                    comparator=target.comparator,
                ),
            ],
        )

    @staticmethod
    def is_value_literal(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer | cst.Float | cst.SimpleString)
