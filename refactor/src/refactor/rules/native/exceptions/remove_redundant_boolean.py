"""Native rule for ``remove-redundant-boolean``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveRedundantBooleanRule(CallRewriteRule):
    rule_id = "remove-redundant-boolean"
    summary = "Remove redundant boolean"
    message = "Remove redundant bool() around an expression"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "bool":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        return node.args[0].value
