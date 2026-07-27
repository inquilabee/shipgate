"""Native rule for ``collection-to-bool``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class CollectionToBoolRule(CallRewriteRule):
    rule_id = "collection-to-bool"
    summary = "Collection to bool"
    message = "Use bool(collection) when an explicit boolean value is needed"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "len":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        return cst.Call(
            func=cst.Name("bool"),
            args=[cst.Arg(value=node.args[0].value)],
        )
