"""Native rule for ``remove-dict-keys``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveDictKeysRule(PatternNativeRule):
    rule_id = "remove-dict-keys"
    kind_value = "refactor"
    summary = "Remove dict keys"
    needle = "remove_dict_keys"
    replacement = "Review dictionary pattern for remove-dict-keys"
