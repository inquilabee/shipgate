"""Native rule for ``merge-isinstance``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeIsinstanceRule(PatternNativeRule):
    rule_id = "merge-isinstance"
    kind_value = "refactor"
    summary = "Merge isinstance"
    needle = "merge_isinstance"
    replacement = "Review Sourcery pattern for merge-isinstance"
