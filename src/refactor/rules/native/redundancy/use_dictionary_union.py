"""Native rule for ``use-dictionary-union``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseDictionaryUnionRule(CallRewriteRule):
    rule_id = "use-dictionary-union"
    summary = "Use dictionary union"
    message = "Use dictionary union instead of dict unpacking"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "dict":
            return None
        if len(node.args) != 2:
            return None
        left, right = node.args
        if left.keyword is not None or left.star:
            return None
        if right.keyword is not None or right.star != "**":
            return None
        return cst.BinaryOperation(left=left.value, operator=cst.BitOr(), right=right.value)
