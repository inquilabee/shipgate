"""Native rule for ``swap-nested-ifs``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import IfRewriteRule, merge_nested_if


class SwapNestedIfsRule(IfRewriteRule):
    rule_id = "swap-nested-ifs"
    summary = "Swap nested ifs"
    message = "Merge nested if statements into one condition"

    @classmethod
    def match_stmt(cls, node: cst.CSTNode) -> cst.BaseStatement | None:
        return merge_nested_if(node)
