"""Native rule for ``method``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MethodRule(PatternNativeRule):
    rule_id = "method"
    kind_value = "refactor"
    summary = "Method"
    needle = ""
    replacement = "method is registered as comment-only"
