"""Native rule for ``use-file-iterator``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseFileIteratorRule(CallRewriteRule):
    rule_id = "use-file-iterator"
    summary = "Use file iterator"
    message = "Iterate over the file object instead of calling readlines()"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if node.args:
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "readlines":
            return None
        return node.func.value
