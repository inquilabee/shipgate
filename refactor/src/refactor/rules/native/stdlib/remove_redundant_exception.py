"""Native rule for ``remove-redundant-exception``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantExceptionRule(PatternNativeRule):
    rule_id = "remove-redundant-exception"
    kind_value = "refactor"
    summary = "Remove redundant exception"
    needle = "remove_redundant_exception"
    replacement = "Review exception pattern for remove-redundant-exception"
