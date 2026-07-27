"""Native rule for ``use-string-remove-affix``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import SubscriptRewriteRule


class UseStringRemoveAffixRule(SubscriptRewriteRule):
    rule_id = "use-string-remove-affix"
    summary = "Use string remove affix"
    message = "Use removeprefix() or removesuffix() for affix slicing"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Subscript) or len(node.slice) != 1:
            return None
        subscript = node.slice[0].slice
        if not isinstance(subscript, cst.Slice):
            return None
        prefix = cls.len_call_arg(subscript.lower)
        if prefix is not None and subscript.upper is None:
            return cls.remove_call(node.value, "removeprefix", prefix)
        suffix = cls.negated_len_call_arg(subscript.upper)
        if suffix is not None and subscript.lower is None:
            return cls.remove_call(node.value, "removesuffix", suffix)
        return None

    @staticmethod
    def remove_call(
        receiver: cst.BaseExpression,
        method_name: str,
        affix: cst.BaseExpression,
    ) -> cst.BaseExpression:
        return cst.Call(
            func=cst.Attribute(value=receiver, attr=cst.Name(method_name)),
            args=[cst.Arg(value=affix)],
        )

    @staticmethod
    def len_call_arg(node: cst.BaseExpression | None) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "len":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        return node.args[0].value

    @classmethod
    def negated_len_call_arg(cls, node: cst.BaseExpression | None) -> cst.BaseExpression | None:
        if not isinstance(node, cst.UnaryOperation) or not isinstance(node.operator, cst.Minus):
            return None
        return cls.len_call_arg(node.expression)
