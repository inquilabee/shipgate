"""Native rule for ``merge-list-appends-into-extend``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeListAppendsIntoExtendRule(PatternNativeRule):
    rule_id = "merge-list-appends-into-extend"
    kind_value = "refactor"
    summary = "Merge list appends into extend"
    needle = "merge_list_appends_into_extend"
    replacement = "Review collection pattern for merge-list-appends-into-extend"
