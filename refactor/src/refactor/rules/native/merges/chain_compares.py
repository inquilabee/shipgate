"""Native rule for ``chain-compares``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import BooleanOpRewriteRule, merge_adjacent_comparisons


class ChainComparesRule(BooleanOpRewriteRule):
    rule_id = "chain-compares"
    summary = "Chain compares"
    message = "Chain adjacent comparisons sharing the middle operand"

    @classmethod
    def match(cls, node: cst.CSTNode) -> cst.BaseExpression | None:
        return merge_adjacent_comparisons(node)
