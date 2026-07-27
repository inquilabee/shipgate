"""Native rule for ``merge-isinstance``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BooleanOpRewriteRule, merge_isinstance_calls


class MergeIsinstanceRule(BooleanOpRewriteRule):
    rule_id = "merge-isinstance"
    summary = "Merge isinstance"
    message = "Merge repeated isinstance() calls for the same subject"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return merge_isinstance_calls(node)
