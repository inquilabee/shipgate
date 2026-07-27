"""Replace ``range(0, n)`` with ``range(n)``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveZeroFromRangeRule(CallRewriteRule):
    rule_id = "remove-zero-from-range"
    summary = "Replace `range(0, n)` with `range(n)`"
    message = "Remove redundant zero start from range()"

    @classmethod
    def match(cls, node: cst.Call) -> cst.BaseExpression | None:
        if not isinstance(node.func, cst.Name) or node.func.value != "range":
            return None
        if len(node.args) != 2:
            return None
        if any(arg.keyword is not None for arg in node.args):
            return None
        start, stop = node.args
        if not isinstance(start.value, cst.Integer) or start.value.value != "0":
            return None
        return node.with_changes(args=[stop.with_changes(comma=cst.MaybeSentinel.DEFAULT)])
