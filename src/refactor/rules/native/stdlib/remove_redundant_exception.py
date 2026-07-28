"""Native rule for ``remove-redundant-exception`` (retired)."""

from __future__ import annotations

import libcst as cst

from refactor.protocol import ApplyMode
from refactor.rules.native.stmt_base import SimpleStatementLineRewriteRule


class RemoveRedundantExceptionRule(SimpleStatementLineRewriteRule):
    """Retired: stripping ``from None`` changes exception chaining semantics."""

    rule_id = "remove-redundant-exception"
    summary = "Remove redundant exception"
    message = "Remove redundant explicit exception cause"
    apply_mode = ApplyMode.OFF
    enabled = False

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        _ = node
        return None
