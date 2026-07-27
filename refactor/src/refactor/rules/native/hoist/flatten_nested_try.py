"""Native rule for ``flatten-nested-try``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class FlattenNestedTryRule(PatternNativeRule):
    rule_id = "flatten-nested-try"
    kind_value = "refactor"
    summary = "Flatten nested try"
    needle = "flatten_nested_try"
    replacement = "Review exception pattern for flatten-nested-try"
