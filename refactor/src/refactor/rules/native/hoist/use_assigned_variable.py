"""Native rule for ``use-assigned-variable``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseAssignedVariableRule(PatternNativeRule):
    rule_id = "use-assigned-variable"
    kind_value = "refactor"
    summary = "Use assigned variable"
    needle = "use_assigned_variable"
    replacement = "Review Sourcery pattern for use-assigned-variable"
