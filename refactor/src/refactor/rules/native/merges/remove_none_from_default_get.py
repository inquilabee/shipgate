"""Native rule for ``remove-none-from-default-get``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_none_name
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveNoneFromDefaultGetRule(CallRewriteRule):
    rule_id = "remove-none-from-default-get"
    summary = "Remove none from default get"
    message = "Remove explicit None default from dict.get()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "get":
            return None
        if len(node.args) != 2 or any(arg.keyword is not None for arg in node.args):
            return None
        if not is_none_name(node.args[1].value):
            return None
        return node.with_changes(args=[node.args[0].with_changes(comma=cst.MaybeSentinel.DEFAULT)])
