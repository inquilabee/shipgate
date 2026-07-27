"""Native rule for ``return-or-yield-outside-function``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class ReturnOrYieldOutsideFunctionRule(PatternNativeRule):
    rule_id = "return-or-yield-outside-function"
    kind_value = "refactor"
    summary = "Return or yield outside function"
    needle = "return_or_yield_outside_function"
    replacement = "Review Sourcery pattern for return-or-yield-outside-function"
