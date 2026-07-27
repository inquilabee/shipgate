"""Native rule for ``hoist-if-from-if``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import IfRewriteRule, merge_nested_if


class HoistIfFromIfRule(IfRewriteRule):
    rule_id = "hoist-if-from-if"
    summary = "Hoist if from if"
    message = "Merge nested if statements into one condition"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        return merge_nested_if(node)
