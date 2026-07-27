"""Native rule for ``max-min-default``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class MaxMinDefaultRule(PatternNativeRule):
    rule_id = "max-min-default"
    kind_value = "refactor"
    summary = "Max min default"
    needle = "max_min_default"
    replacement = "Review Sourcery pattern for max-min-default"
