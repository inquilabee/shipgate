"""Native rule for ``break-or-continue-outside-loop``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class BreakOrContinueOutsideLoopRule(PatternNativeRule):
    rule_id = "break-or-continue-outside-loop"
    kind_value = "refactor"
    summary = "Break or continue outside loop"
    needle = "break_or_continue_outside_loop"
    replacement = "Review loop pattern for break-or-continue-outside-loop"
