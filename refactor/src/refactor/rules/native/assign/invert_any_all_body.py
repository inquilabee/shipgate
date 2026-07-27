"""Native rule for ``invert-any-all-body``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import UnaryOpRewriteRule, invert_any_all_call


class InvertAnyAllBodyRule(UnaryOpRewriteRule):
    rule_id = "invert-any-all-body"
    summary = "Invert any all body"
    message = "Invert any()/all() body instead of negating the call"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return invert_any_all_call(node)
