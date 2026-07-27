"""Replace ``print(str(x))`` with ``print(x)`` for a single argument."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.cst_util import unwrap_str_call
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveStrFromPrintRule(CallRewriteRule):
    rule_id = "remove-str-from-print"
    summary = "Remove redundant str() in print()"
    message = "Remove redundant str() in print()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "print")
        if match is None:
            return None
        call, arg = match
        inner = unwrap_str_call(arg)
        if inner is None:
            return None
        return call.with_changes(args=[call.args[0].with_changes(value=inner)])
