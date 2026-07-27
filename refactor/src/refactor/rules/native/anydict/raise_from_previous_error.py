"""Native rule for ``raise-from-previous-error``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RaiseFromPreviousErrorRule(PatternNativeRule):
    rule_id = "raise-from-previous-error"
    kind_value = "refactor"
    summary = "Raise from previous error"
    needle = "raise_from_previous_error"
    replacement = "Review exception pattern for raise-from-previous-error"
