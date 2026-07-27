"""Native rule for ``remove-duplicate-set-key``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveDuplicateSetKeyRule(PatternNativeRule):
    rule_id = "remove-duplicate-set-key"
    kind_value = "refactor"
    summary = "Remove duplicate set key"
    needle = "remove_duplicate_set_key"
    replacement = "Review dictionary pattern for remove-duplicate-set-key"
