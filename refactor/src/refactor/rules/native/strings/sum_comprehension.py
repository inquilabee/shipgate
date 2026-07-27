"""Native rule for ``sum-comprehension``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SumComprehensionRule(PatternNativeRule):
    rule_id = "sum-comprehension"
    kind_value = "refactor"
    summary = "Sum comprehension"
    needle = "sum_comprehension"
    replacement = "Review Sourcery pattern for sum-comprehension"
