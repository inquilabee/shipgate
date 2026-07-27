"""Native rule for ``merge-is-instance``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BooleanOpRewriteRule, merge_isinstance_calls


class MergeIsInstanceRule(BooleanOpRewriteRule):
    rule_id = "merge-is-instance"
    summary = "Merge is instance"
    message = "Merge repeated isinstance() calls for the same subject"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return merge_isinstance_calls(node)
