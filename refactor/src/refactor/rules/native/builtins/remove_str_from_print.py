"""Replace ``print(str(x))`` with ``print(x)`` for a single argument."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import unwrap_str_call
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveStrFromPrintRule(CallRewriteRule):
    rule_id = "remove-str-from-print"
    summary = "Remove redundant str() in print()"
    message = "Remove redundant str() in print()"

    @classmethod
    def match(cls, node: cst.Call) -> cst.BaseExpression | None:
        if not isinstance(node.func, cst.Name) or node.func.value != "print":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        inner = unwrap_str_call(node.args[0].value)
        if inner is None:
            return None
        return node.with_changes(args=[node.args[0].with_changes(value=inner)])
