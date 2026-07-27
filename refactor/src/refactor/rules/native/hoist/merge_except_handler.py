"""Native rule for ``merge-except-handler``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MergeExceptHandlerRule(PatternNativeRule):
    rule_id = "merge-except-handler"
    kind_value = "refactor"
    summary = "Merge except handler"
    needle = "merge_except_handler"
    replacement = "Review exception pattern for merge-except-handler"
