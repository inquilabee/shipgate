"""Native rule for ``remove-dict-items``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveDictItemsRule(PatternNativeRule):
    rule_id = "remove-dict-items"
    kind_value = "refactor"
    summary = "Remove dict items"
    needle = "remove_dict_items"
    replacement = "Review dictionary pattern for remove-dict-items"
