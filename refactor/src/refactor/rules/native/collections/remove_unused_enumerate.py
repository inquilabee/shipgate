"""Native rule for ``remove-unused-enumerate``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveUnusedEnumerateRule(PatternNativeRule):
    rule_id = "remove-unused-enumerate"
    kind_value = "refactor"
    summary = "Remove unused enumerate"
    needle = "remove_unused_enumerate"
    replacement = "Review Sourcery pattern for remove-unused-enumerate"
