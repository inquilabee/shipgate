"""Native rule for ``use-datetime-now-not-today``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseDatetimeNowNotTodayRule(CallRewriteRule):
    rule_id = "use-datetime-now-not-today"
    summary = "Use datetime now not today"
    message = "Use datetime.now() instead of datetime.today()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call) or node.args:
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "today":
            return None
        if not isinstance(node.func.value, cst.Name | cst.Attribute):
            return None
        return node.with_changes(func=node.func.with_changes(attr=cst.Name("now")))
