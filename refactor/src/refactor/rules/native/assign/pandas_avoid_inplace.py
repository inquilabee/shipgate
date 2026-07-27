"""Native rule for ``pandas-avoid-inplace``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class PandasAvoidInplaceRule(PatternNativeRule):
    rule_id = "pandas-avoid-inplace"
    kind_value = "suggestion"
    summary = "Pandas avoid inplace"
    needle = "pandas_avoid_inplace"
    replacement = "Review pandas pattern for pandas-avoid-inplace"
