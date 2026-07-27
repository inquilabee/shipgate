"""Native rule for ``remove-dict-keys``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class RemoveDictKeysRule(CallRewriteRule):
    rule_id = "remove-dict-keys"
    summary = "Remove dict keys"
    message = "Use the dictionary directly instead of calling keys()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if node.args:
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "keys":
            return None
        return node.func.value
