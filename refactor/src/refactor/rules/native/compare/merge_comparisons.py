"""Native rule for ``merge-comparisons``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BooleanOpRewriteRule, merge_adjacent_comparisons


class MergeComparisonsRule(BooleanOpRewriteRule):
    rule_id = "merge-comparisons"
    summary = "Merge comparisons"
    message = "Merge adjacent comparisons into one chained comparison"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return merge_adjacent_comparisons(node)
