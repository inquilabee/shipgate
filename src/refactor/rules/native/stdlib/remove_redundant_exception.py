"""Native rule for ``remove-redundant-exception``."""

from __future__ import annotations

import libcst as cst

from refactor.cst_util import is_none_name
from refactor.rules.native.stmt_base import SimpleStatementLineRewriteRule


class RemoveRedundantExceptionRule(SimpleStatementLineRewriteRule):
    rule_id = "remove-redundant-exception"
    summary = "Remove redundant exception"
    message = "Remove redundant explicit exception cause"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        if not isinstance(node, cst.Raise):
            return None
        if node.cause is None:
            return None
        if is_none_name(node.cause.item):
            return None
        return None
