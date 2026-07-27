"""Native rule for ``merge-assign-and-aug-assign``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeAssignAndAugAssignRule(PatternNativeRule):
    rule_id = "merge-assign-and-aug-assign"
    kind_value = "refactor"
    summary = "Merge assign and aug assign"
    needle = "merge_assign_and_aug_assign"
    replacement = "Review Sourcery pattern for merge-assign-and-aug-assign"
