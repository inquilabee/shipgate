"""Replace ``xs[len(xs) - 1]`` with ``xs[-1]`` for the same name."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import SubscriptRewriteRule


class SimplifyNegativeIndexRule(SubscriptRewriteRule):
    rule_id = "simplify-negative-index"
    summary = "Replace `xs[len(xs) - 1]` with `xs[-1]`"
    message = "Use negative index instead of len() arithmetic"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Subscript):
            return None
        if not isinstance(node.value, cst.Name):
            return None
        if len(node.slice) != 1:
            return None
        element = node.slice[0]
        if not isinstance(element.slice, cst.Index):
            return None
        if not cls.is_len_minus_one(element.slice.value, node.value.value):
            return None
        negative_index = cst.SubscriptElement(
            slice=cst.Index(
                value=cst.UnaryOperation(
                    operator=cst.Minus(),
                    expression=cst.Integer("1"),
                ),
            ),
        )
        return node.with_changes(slice=[negative_index])

    @staticmethod
    def is_len_minus_one(expr: cst.BaseExpression, name: str) -> bool:
        if not isinstance(expr, cst.BinaryOperation):
            return False
        if not isinstance(expr.operator, cst.Subtract):
            return False
        if not isinstance(expr.right, cst.Integer) or expr.right.value != "1":
            return False
        if not isinstance(expr.left, cst.Call):
            return False
        if not isinstance(expr.left.func, cst.Name) or expr.left.func.value != "len":
            return False
        if len(expr.left.args) != 1 or expr.left.args[0].keyword is not None:
            return False
        subject = expr.left.args[0].value
        return isinstance(subject, cst.Name) and subject.value == name
