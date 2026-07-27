"""Native rule for ``remove-redundant-except-handler``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantExceptHandlerRule(PatternNativeRule):
    rule_id = "remove-redundant-except-handler"
    kind_value = "refactor"
    summary = "Remove redundant except handler"
    needle = "remove_redundant_except_handler"
    replacement = "Review exception pattern for remove-redundant-except-handler"
