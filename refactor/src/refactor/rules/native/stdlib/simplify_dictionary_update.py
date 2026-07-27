"""Native rule for ``simplify-dictionary-update``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import (
    SimpleStatementLineRewriteRule,
    dict_update_to_union_stmt,
)


class SimplifyDictionaryUpdateRule(SimpleStatementLineRewriteRule):
    rule_id = "simplify-dictionary-update"
    summary = "Simplify dictionary update"
    message = "Use dictionary union assignment instead of update"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        return dict_update_to_union_stmt(node)
