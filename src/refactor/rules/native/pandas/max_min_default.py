"""Native rule for ``max-min-default``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import positional_call_any
from refactor.rules.native.expr_base import IfExpRewriteRule


class MaxMinDefaultRule(IfExpRewriteRule):
    rule_id = "max-min-default"
    summary = "Max min default"
    message = "Use the default argument for min() or max()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.IfExp):
            return None
        if not isinstance(node.body, cst.Call):
            return None
        call = positional_call_any(node.body, frozenset({"max", "min"}), 1)
        if call is None:
            return None
        if not call.args[0].value.deep_equals(node.test):
            return None
        return call.with_changes(
            args=[*call.args, cst.Arg(keyword=cst.Name("default"), value=node.orelse)],
        )
