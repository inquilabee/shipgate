"""Native rule for ``comprehension-to-generator``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import positional_call_any
from refactor.rules.native.expr_base import CallRewriteRule


class ComprehensionToGeneratorRule(CallRewriteRule):
    rule_id = "comprehension-to-generator"
    summary = "Comprehension to generator"
    message = "Pass a generator expression instead of a list comprehension"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        call = positional_call_any(node, frozenset({"all", "any"}), 1)
        if call is None:
            return None
        value = call.args[0].value
        if not isinstance(value, cst.ListComp):
            return None
        return call.with_changes(
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
