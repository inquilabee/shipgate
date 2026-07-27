"""Native rule for ``merge-list-append``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeListAppendRule(PatternNativeRule):
    rule_id = "merge-list-append"
    kind_value = "refactor"
    summary = "Merge list append"
    needle = "merge_list_append"
    replacement = "Review collection pattern for merge-list-append"
