"""Native rule for ``invert-any-all``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import UnaryOpRewriteRule, invert_any_all_call


class InvertAnyAllRule(UnaryOpRewriteRule):
    rule_id = "invert-any-all"
    summary = "Invert any all"
    message = "Invert any()/all() instead of negating the call"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return invert_any_all_call(node)
