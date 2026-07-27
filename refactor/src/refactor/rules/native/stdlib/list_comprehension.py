"""Native rule for ``list-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class ListComprehensionRule(CallRewriteRule):
    rule_id = "list-comprehension"
    summary = "List comprehension"
    message = "Use a list comprehension instead of list() around a generator"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "list":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        generator = node.args[0].value
        if not isinstance(generator, cst.GeneratorExp):
            return None
        return cst.ListComp(elt=generator.elt, for_in=generator.for_in)
