"""Native rule for ``remove-dict-items``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveDictItemsRule(CallRewriteRule):
    rule_id = "remove-dict-items"
    summary = "Remove dict items"
    message = "Avoid calling items() before passing a dictionary to dict()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "dict":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        mapping = cls.dict_items_mapping(node.args[0].value)
        if mapping is None:
            return None
        return node.with_changes(args=[cst.Arg(value=mapping)])

    @staticmethod
    def dict_items_mapping(value: cst.BaseExpression) -> cst.BaseExpression | None:
        if not isinstance(value, cst.Call):
            return None
        if not isinstance(value.func, cst.Attribute) or value.func.attr.value != "items":
            return None
        if value.args:
            return None
        return value.func.value
