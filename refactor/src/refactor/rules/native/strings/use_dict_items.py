"""Native rule for ``use-dict-items``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseDictItemsRule(PatternNativeRule):
    rule_id = "use-dict-items"
    kind_value = "refactor"
    summary = "Use dict items"
    needle = "use_dict_items"
    replacement = "Review dictionary pattern for use-dict-items"
