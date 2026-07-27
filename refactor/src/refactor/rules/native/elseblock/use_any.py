"""Native rule for ``use-any``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseAnyRule(PatternNativeRule):
    rule_id = "use-any"
    kind_value = "refactor"
    summary = "Use any"
    needle = "use_any"
    replacement = "Review Sourcery pattern for use-any"
