"""Native rule for ``sum-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class SumComprehensionRule(CallRewriteRule):
    rule_id = "sum-comprehension"
    summary = "Sum comprehension"
    message = "Pass a generator expression to sum() instead of a list comprehension"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "sum":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        value = node.args[0].value
        if not isinstance(value, cst.ListComp):
            return None
        return node.with_changes(
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
