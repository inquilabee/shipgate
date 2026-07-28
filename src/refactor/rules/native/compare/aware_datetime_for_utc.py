"""Native rule for ``aware-datetime-for-utc``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import empty_attribute_call
from refactor.rules.native.expr_base import CallRewriteRule


class AwareDatetimeForUtcRule(CallRewriteRule):
    rule_id = "aware-datetime-for-utc"
    summary = "Aware datetime for utc"
    message = "Use an aware UTC datetime"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        attr = empty_attribute_call(node, "datetime", "utcnow")
        return (
            None
            if attr is None or not isinstance(node, cst.Call)
            else node.with_changes(
                func=attr.with_changes(attr=cst.Name("now")),
                args=[cst.Arg(value=cst.Name("UTC"))],
            )
        )
