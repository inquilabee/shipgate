"""Native rule for ``simplify-len-comparison``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class SimplifyLenComparisonRule(ComparisonRewriteRule):
    rule_id = "simplify-len-comparison"
    summary = "Simplify len comparison"
    message = "Use collection truthiness instead of comparing len() to zero"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        if not isinstance(node.left, cst.Call) or not cls.is_len_call(node.left):
            return None
        subject = node.left.args[0].value
        target = node.comparisons[0]
        if not cls.is_zero(target.comparator):
            return None
        return cls.truthiness_rewrite(target.operator, subject)

    @staticmethod
    def truthiness_rewrite(
        operator: cst.BaseCompOp,
        subject: cst.BaseExpression,
    ) -> cst.BaseExpression | None:
        return (
            cst.UnaryOperation(operator=cst.Not(), expression=subject)
            if isinstance(operator, cst.Equal | cst.LessThanEqual)
            else (subject if isinstance(operator, cst.NotEqual | cst.GreaterThan) else None)
        )

    @staticmethod
    def is_len_call(node: cst.Call) -> bool:
        return (
            isinstance(node.func, cst.Name)
            and node.func.value == "len"
            and len(node.args) == 1
            and node.args[0].keyword is None
        )

    @staticmethod
    def is_zero(node: cst.BaseExpression) -> bool:
        return isinstance(node, cst.Integer) and node.value == "0"
