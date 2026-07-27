"""Native rule for ``inline-variable``."""

from __future__ import annotations

from refactor.rules.native.stmt_base import ReturnAssignedExpressionRule


class InlineVariableRule(ReturnAssignedExpressionRule):
    rule_id = "inline-variable"
    summary = "Inline variable"
    message = "Inline a variable that is immediately returned"
