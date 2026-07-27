"""Replace ``range(a, b, 1)`` with ``range(a, b)``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveUnitStepFromRangeRule(CallRewriteRule):
    rule_id = "remove-unit-step-from-range"
    summary = "Replace `range(a, b, 1)` with `range(a, b)`"
    message = "Remove redundant unit step from range()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        call = positional_call(node, "range", 3)
        if call is None:
            return None
        step = call.args[2]
        if not isinstance(step.value, cst.Integer) or step.value.value != "1":
            return None
        stop = call.args[1]
        trimmed = [call.args[0], stop.with_changes(comma=cst.MaybeSentinel.DEFAULT)]
        return call.with_changes(args=trimmed)
