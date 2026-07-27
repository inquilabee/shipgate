"""Native rule for ``missing-dict-items``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MissingDictItemsRule(PatternNativeRule):
    rule_id = "missing-dict-items"
    kind_value = "refactor"
    summary = "Missing dict items"
    needle = "missing_dict_items"
    replacement = "Review dictionary pattern for missing-dict-items"
