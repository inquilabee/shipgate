"""Native rule for ``remove-duplicate-key``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveDuplicateKeyRule(PatternNativeRule):
    rule_id = "remove-duplicate-key"
    kind_value = "refactor"
    summary = "Remove duplicate key"
    needle = "remove_duplicate_key"
    replacement = "Review dictionary pattern for remove-duplicate-key"
