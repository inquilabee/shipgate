"""Native rule for ``remove-redundant-continue``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantContinueRule(PatternNativeRule):
    rule_id = "remove-redundant-continue"
    kind_value = "refactor"
    summary = "Remove redundant continue"
    needle = "remove_redundant_continue"
    replacement = "Review loop pattern for remove-redundant-continue"
