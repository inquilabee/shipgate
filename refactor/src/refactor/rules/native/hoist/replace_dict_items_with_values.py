"""Native rule for ``replace-dict-items-with-values``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReplaceDictItemsWithValuesRule(PatternNativeRule):
    rule_id = "replace-dict-items-with-values"
    kind_value = "refactor"
    summary = "Replace dict items with values"
    needle = "replace_dict_items_with_values"
    replacement = "Review dictionary pattern for replace-dict-items-with-values"
