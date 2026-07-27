"""Native rule for ``use-any``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class UseAnyRule(CallRewriteRule):
    rule_id = "use-any"
    summary = "Use any"
    message = "Use any() instead of bool() around a list comprehension"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "bool")
        if match is None:
            return None
        _, value = match
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
