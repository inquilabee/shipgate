"""Native rule for ``no-conditionals-in-tests``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class NoConditionalsInTestsRule(PatternNativeRule):
    rule_id = "no-conditionals-in-tests"
    kind_value = "refactor"
    summary = "No conditionals in tests"
    needle = "no_conditionals_in_tests"
    replacement = "Review conditional pattern for no-conditionals-in-tests"
