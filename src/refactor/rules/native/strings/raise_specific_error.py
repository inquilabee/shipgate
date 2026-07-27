"""Native rule for ``raise-specific-error``."""

from __future__ import annotations

import libcst as cst

from refactor.rules.native.stmt_base import SimpleStatementLineRewriteRule


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
        runtime_error = cls.runtime_error_call(node.exc)
        if runtime_error is None:
            return None
        return node.with_changes(exc=runtime_error)

    @staticmethod
    def runtime_error_call(exc: cst.BaseExpression) -> cst.Call | None:
        if not isinstance(exc, cst.Call):
            return None
        if not isinstance(exc.func, cst.Name) or exc.func.value != "Exception":
            return None
        return exc.with_changes(func=cst.Name("RuntimeError"))
