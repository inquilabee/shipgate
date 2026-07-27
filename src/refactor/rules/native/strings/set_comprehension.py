"""Native rule for ``set-comprehension``."""

from __future__ import annotations

import libcst as cst

from refactor.call_match import single_positional_call
from refactor.rules.native.expr_base import CallRewriteRule


class SetComprehensionRule(CallRewriteRule):
    rule_id = "set-comprehension"
    summary = "Set comprehension"
    message = "Use a set comprehension instead of set() around a generator"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        match = single_positional_call(node, "set")
        if match is None:
            return None
        _, generator = match
        if not isinstance(generator, cst.GeneratorExp):
            return None
        return cst.SetComp(elt=generator.elt, for_in=generator.for_in)
