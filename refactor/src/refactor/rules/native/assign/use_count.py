"""Native rule for ``use-count``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class UseCountRule(PatternNativeRule):
    rule_id = "use-count"
    kind_value = "refactor"
    summary = "Use count"
    needle = "use_count"
    replacement = "Review Sourcery pattern for use-count"
