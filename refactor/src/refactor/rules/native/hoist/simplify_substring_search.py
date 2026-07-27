"""Native rule for ``simplify-substring-search``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import ComparisonRewriteRule


class SimplifySubstringSearchRule(ComparisonRewriteRule):
    rule_id = "simplify-substring-search"
    summary = "Simplify substring search"
    message = "Use membership testing instead of comparing find() with -1"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Comparison) or len(node.comparisons) != 1:
            return None
        if not isinstance(node.left, cst.Call):
            return None
        call = node.left
        if not isinstance(call.func, cst.Attribute) or call.func.attr.value != "find":
            return None
        if len(call.args) != 1 or call.args[0].keyword is not None:
            return None
        target = node.comparisons[0]
        if not cls.is_negative_one(target.comparator):
            return None
        if isinstance(target.operator, cst.NotEqual):
            operator: cst.BaseCompOp = cst.In()
        elif isinstance(target.operator, cst.Equal):
            operator = cst.NotIn()
        else:
            return None
        return cst.Comparison(
            left=call.args[0].value,
            comparisons=[
                cst.ComparisonTarget(
                    operator=operator,
                    comparator=call.func.value,
                ),
            ],
        )

    @staticmethod
    def is_negative_one(node: cst.BaseExpression) -> bool:
        return (
            isinstance(node, cst.UnaryOperation)
            and isinstance(node.operator, cst.Minus)
            and isinstance(node.expression, cst.Integer)
            and node.expression.value == "1"
        )
