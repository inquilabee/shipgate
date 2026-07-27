"""Native rule for ``remove-none-from-default-get``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import two_positional_method_call
from refactor.cst_util import is_none_name
from refactor.rules.native.expr_base import CallRewriteRule


class RemoveNoneFromDefaultGetRule(CallRewriteRule):
    rule_id = "remove-none-from-default-get"
    summary = "Remove none from default get"
    message = "Remove explicit None default from dict.get()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = two_positional_method_call(node, "get")
        if match is None:
            return None
        call, _, _, default = match
        if not is_none_name(default):
            return None
        return call.with_changes(
            args=[call.args[0].with_changes(comma=cst.MaybeSentinel.DEFAULT)],
        )
