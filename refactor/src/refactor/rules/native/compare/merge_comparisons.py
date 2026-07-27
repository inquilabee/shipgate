"""Native rule for ``merge-comparisons``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeComparisonsRule(PatternNativeRule):
    rule_id = "merge-comparisons"
    kind_value = "refactor"
    summary = "Merge comparisons"
    needle = "merge_comparisons"
    replacement = "Review comparison pattern for merge-comparisons"
