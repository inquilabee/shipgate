"""Native rule for ``merge-duplicate-blocks``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeDuplicateBlocksRule(PatternNativeRule):
    rule_id = "merge-duplicate-blocks"
    kind_value = "refactor"
    summary = "Merge duplicate blocks"
    needle = "merge_duplicate_blocks"
    replacement = "Review Sourcery pattern for merge-duplicate-blocks"
