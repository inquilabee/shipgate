"""Native rule for ``simplify-single-exception-tuple``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class SimplifySingleExceptionTupleRule(PatternNativeRule):
    rule_id = "simplify-single-exception-tuple"
    kind_value = "refactor"
    summary = "Simplify single exception tuple"
    needle = "simplify_single_exception_tuple"
    replacement = "Review exception pattern for simplify-single-exception-tuple"
