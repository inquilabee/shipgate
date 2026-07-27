"""Native rule for ``aware-datetime-for-utc``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class AwareDatetimeForUtcRule(CallRewriteRule):
    rule_id = "aware-datetime-for-utc"
    summary = "Aware datetime for utc"
    message = "Use an aware UTC datetime"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call) or node.args:
            return None
        if not isinstance(node.func, cst.Attribute):
            return None
        if not isinstance(node.func.value, cst.Name) or node.func.value.value != "datetime":
            return None
        if node.func.attr.value != "utcnow":
            return None
        return node.with_changes(
            func=node.func.with_changes(attr=cst.Name("now")),
            args=[cst.Arg(value=cst.Name("UTC"))],
        )
