"""Native rule for ``skip-sorted-list-construction``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class SkipSortedListConstructionRule(CallRewriteRule):
    rule_id = "skip-sorted-list-construction"
    summary = "Skip sorted list construction"
    message = "Pass the iterable directly to sorted() instead of wrapping it in list()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "sorted")
        if match is None:
            return None
        call, _ = match
        wrapped = cls.list_wrapped_arg(call)
        if wrapped is None:
            return None
        return call.with_changes(args=[wrapped, *call.args[1:]])

    @staticmethod
    def list_wrapped_arg(node: cst.Call) -> cst.Arg | None:
        if not node.args:
            return None
        first_arg = node.args[0]
        if first_arg.keyword is not None or not isinstance(first_arg.value, cst.Call):
            return None
        inner_match = single_positional_call(first_arg.value, "list")
        if inner_match is None:
            return None
        _, value = inner_match
        return first_arg.with_changes(value=value)
