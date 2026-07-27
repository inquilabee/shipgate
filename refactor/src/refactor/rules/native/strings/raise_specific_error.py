"""Native rule for ``raise-specific-error``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.expr_base import SimpleStatementLineRewriteRule


class RaiseSpecificErrorRule(SimpleStatementLineRewriteRule):
    rule_id = "raise-specific-error"
    summary = "Raise specific error"
    message = "Raise a more specific exception type"

    @classmethod
    def match_small_stmt(cls, node: cst.BaseSmallStatement) -> cst.BaseSmallStatement | None:
        if not isinstance(node, cst.Raise) or node.exc is None:
            return None
        if isinstance(node.exc, cst.Name) and node.exc.value == "Exception":
            return node.with_changes(exc=cst.Name("RuntimeError"))
        if not isinstance(node.exc, cst.Call):
            return None
        if not isinstance(node.exc.func, cst.Name) or node.exc.func.value != "Exception":
            return None
        return node.with_changes(exc=node.exc.with_changes(func=cst.Name("RuntimeError")))
