"""Native rule for ``use-join``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BinaryOpRewriteRule


class UseJoinRule(BinaryOpRewriteRule):
    rule_id = "use-join"
    summary = "Use join"
    message = "Use ''.join() for simple string concatenation chains"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.BinaryOperation):
            return None
        parts = cls.string_parts(node)
        if len(parts) < 3:
            return None
        return cst.Call(
            func=cst.Attribute(value=cst.SimpleString('""'), attr=cst.Name("join")),
            args=[
                cst.Arg(
                    value=cst.List(elements=[cst.Element(value=part) for part in parts]),
                ),
            ],
        )

    @classmethod
    def string_parts(cls, node: cst.BaseExpression) -> list[cst.BaseExpression]:
        if isinstance(node, cst.BinaryOperation) and isinstance(node.operator, cst.Add):
            return [*cls.string_parts(node.left), *cls.string_parts(node.right)]
        if isinstance(node, cst.Name | cst.Attribute | cst.Subscript | cst.SimpleString):
            return [node]
        return []
