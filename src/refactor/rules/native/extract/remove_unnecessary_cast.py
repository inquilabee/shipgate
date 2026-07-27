"""Native rule for ``remove-unnecessary-cast``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveUnnecessaryCastRule(CallRewriteRule):
    rule_id = "remove-unnecessary-cast"
    summary = "Remove unnecessary cast"
    message = "Remove redundant typing.cast around a value"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not cls.is_cast_func(node.func):
            return None
        if len(node.args) != 2 or any(arg.keyword is not None for arg in node.args):
            return None
        return node.args[1].value

    @staticmethod
    def is_cast_func(node: cst.BaseExpression) -> bool:
        if isinstance(node, cst.Name):
            return node.value == "cast"
        return (
            isinstance(node, cst.Attribute)
            and isinstance(node.value, cst.Name)
            and node.value.value == "typing"
            and node.attr.value == "cast"
        )
