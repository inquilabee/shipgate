"""Native rule for ``set-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class SetComprehensionRule(CallRewriteRule):
    rule_id = "set-comprehension"
    summary = "Set comprehension"
    message = "Use a set comprehension instead of set() around a generator"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "set":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        generator = node.args[0].value
        if not isinstance(generator, cst.GeneratorExp):
            return None
        return cst.SetComp(elt=generator.elt, for_in=generator.for_in)
