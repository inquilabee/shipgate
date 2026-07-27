"""Native rule for ``replace-apply-with-method-call``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class ReplaceApplyWithMethodCallRule(CallRewriteRule):
    rule_id = "replace-apply-with-method-call"
    summary = "Replace apply with method call"
    message = "Use the pandas string accessor instead of apply(str.method)"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "apply":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        applied = node.args[0].value
        if not isinstance(applied, cst.Attribute):
            return None
        if not isinstance(applied.value, cst.Name) or applied.value.value != "str":
            return None
        return cst.Call(
            func=cst.Attribute(
                value=cst.Attribute(value=node.func.value, attr=cst.Name("str")),
                attr=applied.attr,
            ),
        )
