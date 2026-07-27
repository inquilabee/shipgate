"""Native rule for ``merge-else-if-into-elif``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeElseIfIntoElifRule(PatternNativeRule):
    rule_id = "merge-else-if-into-elif"
    kind_value = "refactor"
    summary = "Merge else if into elif"
    needle = "merge_else_if_into_elif"
    replacement = "Review conditional pattern for merge-else-if-into-elif"
