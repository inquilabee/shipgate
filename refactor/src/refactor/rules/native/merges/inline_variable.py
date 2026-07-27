"""Native rule for ``inline-variable``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class InlineVariableRule(PatternNativeRule):
    rule_id = "inline-variable"
    kind_value = "refactor"
    summary = "Inline variable"
    needle = "inline_variable"
    replacement = "Review Sourcery pattern for inline-variable"
