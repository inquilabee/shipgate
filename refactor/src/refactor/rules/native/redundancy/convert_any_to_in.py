"""Native rule for ``convert-any-to-in``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ConvertAnyToInRule(PatternNativeRule):
    rule_id = "convert-any-to-in"
    kind_value = "refactor"
    summary = "Convert any to in"
    needle = "convert_any_to_in"
    replacement = "Review Sourcery pattern for convert-any-to-in"
