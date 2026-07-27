"""Native rule for ``compare-via-equals``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class CompareViaEqualsRule(PatternNativeRule):
    rule_id = "compare-via-equals"
    kind_value = "refactor"
    summary = "Compare via equals"
    needle = "compare_via_equals"
    replacement = "Review comparison pattern for compare-via-equals"
