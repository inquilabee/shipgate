"""Native rule for ``merge-is-instance``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeIsInstanceRule(PatternNativeRule):
    rule_id = "merge-is-instance"
    kind_value = "refactor"
    summary = "Merge is instance"
    needle = "merge_is_instance"
    replacement = "Review Sourcery pattern for merge-is-instance"
