"""Replace ``range(a, b, 1)`` with ``range(a, b)``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveUnitStepFromRangeRule(CallRewriteRule):
    rule_id = "remove-unit-step-from-range"
    summary = "Replace `range(a, b, 1)` with `range(a, b)`"
    message = "Remove redundant unit step from range()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "range":
            return None
        if len(node.args) != 3:
            return None
        if any(arg.keyword is not None for arg in node.args):
            return None
        step = node.args[2]
        if not isinstance(step.value, cst.Integer) or step.value.value != "1":
            return None
        stop = node.args[1]
        trimmed = [node.args[0], stop.with_changes(comma=cst.MaybeSentinel.DEFAULT)]
        return node.with_changes(args=trimmed)
