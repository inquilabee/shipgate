"""Native rule for ``skip-sorted-list-construction``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class SkipSortedListConstructionRule(CallRewriteRule):
    rule_id = "skip-sorted-list-construction"
    summary = "Skip sorted list construction"
    message = "Pass the iterable directly to sorted() instead of wrapping it in list()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "sorted":
            return None
        if not node.args:
            return None
        first_arg = node.args[0]
        if first_arg.keyword is not None or not isinstance(first_arg.value, cst.Call):
            return None
        inner = first_arg.value
        if not isinstance(inner.func, cst.Name) or inner.func.value != "list":
            return None
        if len(inner.args) != 1 or inner.args[0].keyword is not None:
            return None
        return node.with_changes(
            args=[first_arg.with_changes(value=inner.args[0].value), *node.args[1:]],
        )
