"""Native rule for ``raise-specific-error``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RaiseSpecificErrorRule(PatternNativeRule):
    rule_id = "raise-specific-error"
    kind_value = "refactor"
    summary = "Raise specific error"
    needle = "raise_specific_error"
    replacement = "Review exception pattern for raise-specific-error"
