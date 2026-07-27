"""Native rule for ``unwrap-iterable-construction``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UnwrapIterableConstructionRule(CallRewriteRule):
    rule_id = "unwrap-iterable-construction"
    summary = "Unwrap iterable construction"
    message = "Remove redundant collection construction around the same literal type"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        if not isinstance(node.func, cst.Name):
            return None
        value = node.args[0].value
        if node.func.value == "list" and isinstance(value, cst.List):
            return value
        if node.func.value == "tuple" and isinstance(value, cst.Tuple):
            return value
        if node.func.value == "set" and isinstance(value, cst.Set):
            return value
        return None
