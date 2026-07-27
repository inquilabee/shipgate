"""Native rule for ``merge-list-extend``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeListExtendRule(PatternNativeRule):
    rule_id = "merge-list-extend"
    kind_value = "refactor"
    summary = "Merge list extend"
    needle = "merge_list_extend"
    replacement = "Review collection pattern for merge-list-extend"
