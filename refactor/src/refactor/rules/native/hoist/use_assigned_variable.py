"""Native rule for ``use-assigned-variable``."""

from __future__ import annotations

from refactor.rules.native.stmt_base import ReturnAssignedExpressionRule


class UseAssignedVariableRule(ReturnAssignedExpressionRule):
    rule_id = "use-assigned-variable"
    summary = "Use assigned variable"
    message = "Use the assigned expression directly"
