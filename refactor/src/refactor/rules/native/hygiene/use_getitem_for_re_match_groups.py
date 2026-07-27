"""Native rule for ``use-getitem-for-re-match-groups``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseGetitemForReMatchGroupsRule(CallRewriteRule):
    rule_id = "use-getitem-for-re-match-groups"
    summary = "Use getitem for re match groups"
    message = "Use subscript access for regular expression match groups"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "group":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        if not isinstance(node.args[0].value, cst.Integer | cst.SimpleString):
            return None
        return cst.Subscript(
            value=node.func.value,
            slice=[cst.SubscriptElement(slice=cst.Index(value=node.args[0].value))],
        )
