"""Native rule for ``remove-redundant-boolean``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveRedundantBooleanRule(PatternNativeRule):
    rule_id = "remove-redundant-boolean"
    kind_value = "refactor"
    summary = "Remove redundant boolean"
    needle = "remove_redundant_boolean"
    replacement = "Review Sourcery pattern for remove-redundant-boolean"
