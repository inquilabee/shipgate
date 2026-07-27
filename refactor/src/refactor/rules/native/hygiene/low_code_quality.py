"""Native rule for ``low-code-quality``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class LowCodeQualityRule(PatternNativeRule):
    rule_id = "low-code-quality"
    kind_value = "comment"
    summary = "Low code quality"
    needle = ""
    replacement = "low-code-quality is registered as comment-only"
