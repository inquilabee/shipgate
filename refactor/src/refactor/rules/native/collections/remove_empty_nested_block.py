"""Native rule for ``remove-empty-nested-block``."""

from __future__ import annotations

from refactor.rules.native.pattern_base import PatternNativeRule


class RemoveEmptyNestedBlockRule(PatternNativeRule):
    rule_id = "remove-empty-nested-block"
    kind_value = "refactor"
    summary = "Remove empty nested block"
    needle = "remove_empty_nested_block"
    replacement = "Review Sourcery pattern for remove-empty-nested-block"
