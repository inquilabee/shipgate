"""Native rule for ``invert-any-all``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class InvertAnyAllRule(PatternNativeRule):
    rule_id = "invert-any-all"
    kind_value = "refactor"
    summary = "Invert any all"
    needle = "invert_any_all"
    replacement = "Review Sourcery pattern for invert-any-all"
