"""Native rule for ``replace-apply-with-numpy-operation``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class ReplaceApplyWithNumpyOperationRule(CallRewriteRule):
    rule_id = "replace-apply-with-numpy-operation"
    summary = "Replace apply with numpy operation"
    message = "Call numpy operations on the series directly instead of using apply()"

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
        if not isinstance(applied.value, cst.Name) or applied.value.value not in {"np", "numpy"}:
            return None
        return cst.Call(func=applied, args=[cst.Arg(value=node.func.value)])
