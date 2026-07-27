"""Native rule for ``dict-assign-update-to-union``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import (
    SimpleStatementLineRewriteRule,
    dict_update_to_union_stmt,
)


class DictAssignUpdateToUnionRule(SimpleStatementLineRewriteRule):
    rule_id = "dict-assign-update-to-union"
    summary = "Dict assign update to union"
    message = "Use dictionary union assignment instead of update"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        return dict_update_to_union_stmt(node)
