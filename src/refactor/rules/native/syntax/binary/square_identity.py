"""Replace ``x * x`` with ``x ** 2`` when both operands are the same name."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BinaryOpRewriteRule


class SquareIdentityRule(BinaryOpRewriteRule):
    rule_id = "square-identity"
    summary = "Replace `x * x` with `x ** 2`"
    message = "Use exponentiation for squaring"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BinaryOperation):
            return None
        if not isinstance(node.operator, cst.Multiply):
            return None
        if not isinstance(node.left, cst.Name) or not isinstance(node.right, cst.Name):
            return None
        if node.left.value != node.right.value:
            return None
        return cst.BinaryOperation(
            left=node.left,
            operator=cst.Power(
                whitespace_before=cst.SimpleWhitespace(" "),
                whitespace_after=cst.SimpleWhitespace(" "),
            ),
            right=cst.Integer("2"),
        )
