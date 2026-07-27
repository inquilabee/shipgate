"""Native rule for ``merge-repeated-ifs``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeRepeatedIfsRule(PatternNativeRule):
    rule_id = "merge-repeated-ifs"
    kind_value = "refactor"
    summary = "Merge repeated ifs"
    needle = "merge_repeated_ifs"
    replacement = "Review conditional pattern for merge-repeated-ifs"
