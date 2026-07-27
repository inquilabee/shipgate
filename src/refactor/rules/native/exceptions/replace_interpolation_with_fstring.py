"""Native rule for ``replace-interpolation-with-fstring``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BinaryOpRewriteRule


class ReplaceInterpolationWithFstringRule(BinaryOpRewriteRule):
    rule_id = "replace-interpolation-with-fstring"
    summary = "Replace interpolation with fstring"
    message = "Use an f-string instead of percent interpolation"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BinaryOperation) or not isinstance(node.operator, cst.Modulo):
            return None
        if not isinstance(node.left, cst.SimpleString) or node.left.evaluated_value != "%s":
            return None
        return cst.FormattedString(
            parts=[cst.FormattedStringExpression(expression=node.right)],
        )
