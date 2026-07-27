"""Native rule for ``use-getitem-for-re-match-groups``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_method_call
from refactor.rules.native.expr_base import CallRewriteRule


class UseGetitemForReMatchGroupsRule(CallRewriteRule):
    rule_id = "use-getitem-for-re-match-groups"
    summary = "Use getitem for re match groups"
    message = "Use subscript access for regular expression match groups"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_method_call(node, "group")
        if match is None:
            return None
        _, attr, arg_value = match
        if not isinstance(arg_value, cst.Integer | cst.SimpleString):
            return None
        return cst.Subscript(
            value=attr.value,
            slice=[cst.SubscriptElement(slice=cst.Index(value=arg_value))],
        )
