"""Native rule for ``remove-pass-elif``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemovePassElifRule(PatternNativeRule):
    rule_id = "remove-pass-elif"
    kind_value = "refactor"
    summary = "Remove pass elif"
    needle = "remove_pass_elif"
    replacement = "Review conditional pattern for remove-pass-elif"
