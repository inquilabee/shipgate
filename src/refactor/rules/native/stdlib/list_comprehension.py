"""Native rule for ``list-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class ListComprehensionRule(CallRewriteRule):
    rule_id = "list-comprehension"
    summary = "List comprehension"
    message = "Use a list comprehension instead of list() around a generator"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "list")
        if match is None:
            return None
        _, generator = match
        if not isinstance(generator, cst.GeneratorExp):
            return None
        return cst.ListComp(elt=generator.elt, for_in=generator.for_in)
