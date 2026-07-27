"""Native rule for ``collection-builtin-to-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import CallRewriteRule


class CollectionBuiltinToComprehensionRule(CallRewriteRule):
    rule_id = "collection-builtin-to-comprehension"
    summary = "Collection builtin to comprehension"
    message = "Use a dict comprehension instead of dict() around a generator"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        if not isinstance(node, cst.Call):
            return None
        if not isinstance(node.func, cst.Name) or node.func.value != "dict":
            return None
        if len(node.args) != 1 or node.args[0].keyword is not None:
            return None
        generator = node.args[0].value
        if not isinstance(generator, cst.GeneratorExp):
            return None
        if not isinstance(generator.elt, cst.Tuple) or len(generator.elt.elements) != 2:
            return None
        return cst.DictComp(
            key=generator.elt.elements[0].value,
            value=generator.elt.elements[1].value,
            for_in=generator.for_in,
        )
