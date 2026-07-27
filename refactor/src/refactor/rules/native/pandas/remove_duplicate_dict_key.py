"""Native rule for ``remove-duplicate-dict-key``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveDuplicateDictKeyRule(PatternNativeRule):
    rule_id = "remove-duplicate-dict-key"
    kind_value = "suggestion"
    summary = "Remove duplicate dict key"
    needle = "remove_duplicate_dict_key"
    replacement = "Review dictionary pattern for remove-duplicate-dict-key"
