"""Native rule for ``sum-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class SumComprehensionRule(CallRewriteRule):
    rule_id = "sum-comprehension"
    summary = "Sum comprehension"
    message = "Pass a generator expression to sum() instead of a list comprehension"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "sum")
        if match is None:
            return None
        _, value = match
        if not isinstance(value, cst.ListComp):
            return None
        return match[0].with_changes(
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
