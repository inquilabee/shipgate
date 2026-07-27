"""Native rule for ``simplify-constant-sum``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import parse_integer_literal
from refactor.rules.native.expr_base import BinaryOpRewriteRule


class SimplifyConstantSumRule(BinaryOpRewriteRule):
    rule_id = "simplify-constant-sum"
    summary = "Simplify constant sum"
    message = "Replace arithmetic on integer constants with the computed value"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BinaryOperation):
            return None
        left = cls.integer_value(node.left)
        right = cls.integer_value(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.operator, cst.Add):
            return cst.Integer(str(left + right))
        if isinstance(node.operator, cst.Subtract):
            return cst.Integer(str(left - right))
        return None

    @staticmethod
    def integer_value(node: cst.BaseExpression) -> int | None:
        if not isinstance(node, cst.Integer):
            return None
        return parse_integer_literal(node.value)
