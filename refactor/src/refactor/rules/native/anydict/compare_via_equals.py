"""Native rule for ``compare-via-equals``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class CompareViaEqualsRule(CallRewriteRule):
    rule_id = "compare-via-equals"
    summary = "Compare via equals"
    message = "Use == instead of calling __eq__ directly"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Attribute) or node.func.attr.value != "__eq__":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        return cst.Comparison(
            left=node.func.value,
            comparisons=[
                cst.ComparisonTarget(
                    operator=cst.Equal(),
                    comparator=node.args[0].value,
                ),
            ],
        )
