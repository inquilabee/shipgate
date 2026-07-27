"""Replace ``x / 1`` and ``x // 1`` with ``x``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BinaryOpRewriteRule


class SimplifyDivisionRule(BinaryOpRewriteRule):
    rule_id = "simplify-division"
    summary = "Remove division by one"
    message = "Remove division by one"

    @classmethod
    def match(cls, node: cst.BinaryOperation) -> cst.BaseExpression | None:
        if not isinstance(node.operator, (cst.Divide, cst.FloorDivide)):
            return None
        if not isinstance(node.right, cst.Integer) or node.right.value != "1":
            return None
        return node.left
