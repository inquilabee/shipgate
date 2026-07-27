"""Replace ``range(0, n)`` with ``range(n)``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveZeroFromRangeRule(CallRewriteRule):
    rule_id = "remove-zero-from-range"
    summary = "Replace `range(0, n)` with `range(n)`"
    message = "Remove redundant zero start from range()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        call = positional_call(node, "range", 2)
        if call is None:
            return None
        start, stop = call.args
        if not isinstance(start.value, cst.Integer) or start.value.value != "0":
            return None
        return call.with_changes(args=[stop.with_changes(comma=cst.MaybeSentinel.DEFAULT)])
