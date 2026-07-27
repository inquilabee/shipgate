"""Native rule for ``merge-set-add``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeSetAddRule(PatternNativeRule):
    rule_id = "merge-set-add"
    kind_value = "refactor"
    summary = "Merge set add"
    needle = "merge_set_add"
    replacement = "Review collection pattern for merge-set-add"
