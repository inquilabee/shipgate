"""Native rule for ``merge-dict-assign``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeDictAssignRule(PatternNativeRule):
    rule_id = "merge-dict-assign"
    kind_value = "refactor"
    summary = "Merge dict assign"
    needle = "merge_dict_assign"
    replacement = "Review dictionary pattern for merge-dict-assign"
