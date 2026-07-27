"""Native rule for ``no-loop-in-tests``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class NoLoopInTestsRule(PatternNativeRule):
    rule_id = "no-loop-in-tests"
    kind_value = "refactor"
    summary = "No loop in tests"
    needle = "no_loop_in_tests"
    replacement = "Review loop pattern for no-loop-in-tests"
