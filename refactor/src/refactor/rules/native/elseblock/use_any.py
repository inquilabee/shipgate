"""Native rule for ``use-any``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class UseAnyRule(CallRewriteRule):
    rule_id = "use-any"
    summary = "Use any"
    message = "Use any() instead of bool() around a list comprehension"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "bool":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        value = node.args[0].value
        if not isinstance(value, cst.ListComp):
            return None
        return cst.Call(
            func=cst.Name("any"),
            args=[
                cst.Arg(
                    value=cst.GeneratorExp(
                        elt=value.elt,
                        for_in=value.for_in,
                        lpar=[],
                        rpar=[],
                    ),
                ),
            ],
        )
